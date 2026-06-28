from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, AnalysisHistory
from joblib import load
import os
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='templates', static_folder='static')

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this-for-production')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Global model variables
vec = None
clf = None

def load_model():
    """Load ML model and vectorizer"""
    global vec, clf
    try:
        if os.path.exists('model.joblib') and os.path.exists('vectorizer.joblib'):
            vec = load('vectorizer.joblib')
            clf = load('model.joblib')
            return True
    except Exception as e:
        print(f"Error loading model: {e}")
    return False

@login_manager.user_loader
def load_user(user_id):
    """Load user from Firestore by ID"""
    return User.get_by_id(user_id)

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        # Validation
        if not username or not email or not password:
            flash('Please fill in all fields', 'danger')
            return redirect(url_for('register'))
        
        if password != password_confirm:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return redirect(url_for('register'))
        
        if User.find_by_username(username):
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        if User.find_by_email(email):
            flash('Email already exists', 'danger')
            return redirect(url_for('register'))
        
        # Create new user
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            
            if user.save():
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Registration failed. Please try again.', 'danger')
        except Exception as e:
            flash(f'Error during registration: {str(e)}', 'danger')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = User.find_by_username(username)
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Display user dashboard with statistics"""
    try:
        # Get statistics
        total_analyses = AnalysisHistory.count_user_analyses(current_user.id)
        fake_count = AnalysisHistory.count_by_prediction(current_user.id, 'Fake')
        real_count = AnalysisHistory.count_by_prediction(current_user.id, 'Real')
        
        # Get recent analyses
        recent_analyses = AnalysisHistory.get_user_analyses(current_user.id, limit=10, offset=0)
        
        # Get daily stats
        daily_stats = AnalysisHistory.get_daily_stats(current_user.id)
        
        return render_template('dashboard.html', 
                             total_analyses=total_analyses,
                             fake_count=fake_count,
                             real_count=real_count,
                             recent_analyses=recent_analyses,
                             daily_stats=daily_stats)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return render_template('dashboard.html', 
                             total_analyses=0,
                             fake_count=0,
                             real_count=0,
                             recent_analyses=[],
                             daily_stats={})

@app.route('/analyze', methods=['GET', 'POST'])
@login_required
def analyze():
    """Analyze news article for fake news"""
    result = None
    
    if request.method == 'POST':
        if not vec or not clf:
            flash('Model not loaded. Please try again later.', 'danger')
            return render_template('analyze.html', result=result)
        
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        if not title or not content:
            flash('Please enter both title and content', 'warning')
            return render_template('analyze.html', result=result, title=title, content=content)
        
        # Combine title and content for analysis
        text = ' '.join([title, content])
        
        # Get prediction
        try:
            X = vec.transform([text])
            confidence = float(clf.predict_proba(X)[0][1])
            label = clf.predict(X)[0]
            prediction = 'Fake' if label == 1 else 'Real'
            
            result = {
                'label': prediction,
                'confidence': round(confidence * 100, 2),
                'title': title,
                'content': content
            }
            
            # Save to Firestore
            analysis = AnalysisHistory(
                user_id=current_user.id,
                title=title,
                content=content,
                prediction=prediction,
                confidence=confidence
            )
            
            if analysis.save():
                flash(f'Analysis complete! Prediction: {prediction}', 'success')
            else:
                flash('Analysis saved locally but could not sync to database', 'warning')
        
        except Exception as e:
            flash(f'Error during analysis: {str(e)}', 'danger')
    
    return render_template('analyze.html', result=result)

@app.route('/history')
@login_required
def history():
    """Display user's analysis history"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        offset = (page - 1) * per_page
        
        analyses = AnalysisHistory.get_user_analyses(current_user.id, limit=per_page, offset=offset)
        total = AnalysisHistory.count_user_analyses(current_user.id)
        total_pages = (total + per_page - 1) // per_page
        
        class PaginationObj:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1
                self.next_num = page + 1
            
            def iter_pages(self):
                for p in range(1, self.pages + 1):
                    if p == self.page:
                        yield p
                    elif p == 1 or p == self.pages or (p >= self.page - 1 and p <= self.page + 1):
                        yield p
                    elif p == 2 or p == self.pages - 1:
                        yield None
        
        pagination = PaginationObj(analyses, page, per_page, total)
        return render_template('history.html', analyses=pagination)
    
    except Exception as e:
        flash(f'Error loading history: {str(e)}', 'danger')
        return render_template('history.html', analyses=None)

@app.route('/api/analysis-stats')
@login_required
def api_analysis_stats():
    """API endpoint for analysis statistics"""
    try:
        fake_count = AnalysisHistory.count_by_prediction(current_user.id, 'Fake')
        real_count = AnalysisHistory.count_by_prediction(current_user.id, 'Real')
        
        return jsonify({
            'fake': fake_count,
            'real': real_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete-history/<string:analysis_id>', methods=['POST'])
@login_required
def delete_history(analysis_id):
    """Delete an analysis from history"""
    try:
        analysis = AnalysisHistory.get_by_id(analysis_id)
        
        if not analysis or analysis.user_id != current_user.id:
            flash('Analysis not found', 'danger')
            return redirect(url_for('history'))
        
        if analysis.delete():
            flash('Analysis deleted successfully', 'info')
        else:
            flash('Failed to delete analysis', 'danger')
        
        return redirect(url_for('history'))
    
    except Exception as e:
        flash(f'Error deleting analysis: {str(e)}', 'danger')
        return redirect(url_for('history'))

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Load ML model
    if not os.path.exists('model.joblib') or not os.path.exists('vectorizer.joblib'):
        print('⚠️  Model files not found. Run: python train_and_save.py')
    else:
        if load_model():
            print('✓ Model loaded successfully')
        else:
            print('⚠️  Failed to load model')
    
    # Check Firestore connection
    if db is not None:
        print('✓ Firestore connected successfully')
    else:
        print('⚠️  Firestore is unavailable. The app will use an in-memory fallback store until Firebase credentials are configured.')
    
    app.run(
        debug=os.getenv('FLASK_DEBUG', '0') == '1',
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000))
    )
