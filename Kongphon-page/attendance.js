const attendanceKey = 'attendanceRecords';

const allowedLocation = {
  name: 'มรภ.เทพสตรี',
  lat: 14.780523,
  lng: 100.697160,
  radius: 1000 // 1 กิโลเมตร
};

const attendanceStatus = document.getElementById('attendanceStatus');
const attendanceTableBody = document.getElementById('attendanceTableBody');
const checkInButton = document.getElementById('checkInButton');
const clearRecordsButton = document.getElementById('clearRecordsButton');
const studentNameInput = document.getElementById('studentName');

let map;
let campusMarker;
let campusCircle;
let userMarker;

function showStatus(message, type = 'info') {
  attendanceStatus.textContent = message;
  attendanceStatus.style.color = type === 'error' ? '#b91c1c' : '#0f766e';
}

function getStoredRecords() {
  const raw = localStorage.getItem(attendanceKey);
  return raw ? JSON.parse(raw) : [];
}

function saveRecords(records) {
  localStorage.setItem(attendanceKey, JSON.stringify(records));
}

function formatDateTime(date) {
  return new Date(date).toLocaleString('th-TH', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function getDistanceMeters(lat1, lon1, lat2, lon2) {
  const toRad = (value) => (value * Math.PI) / 180;
  const R = 6371000;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function renderRecords() {
  const records = getStoredRecords();
  attendanceTableBody.innerHTML = '';

  if (!records.length) {
    attendanceTableBody.innerHTML = '<tr><td colspan="4">ยังไม่มีการเช็คชื่อ</td></tr>';
    return;
  }

  records.slice().reverse().forEach((record) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${formatDateTime(record.timestamp)}</td>
      <td>${record.name}</td>
      <td>${record.status}</td>
      <td>${record.distance} เมตร</td>
    `;
    attendanceTableBody.appendChild(row);
  });
}

function addRecord(name, status, distance) {
  const records = getStoredRecords();
  records.push({
    timestamp: new Date().toISOString(),
    name,
    status,
    distance
  });
  saveRecords(records);
  renderRecords();
}

function handleLocationError(error) {
  switch (error.code) {
    case error.PERMISSION_DENIED:
      showStatus('ผู้ใช้ปฏิเสธการเข้าถึงตำแหน่ง โปรดอนุญาตให้เบราว์เซอร์เข้าถึง', 'error');
      break;
    case error.POSITION_UNAVAILABLE:
      showStatus('ไม่สามารถระบุตำแหน่งได้ ลองใหม่อีกครั้ง', 'error');
      break;
    case error.TIMEOUT:
      showStatus('หมดเวลาในการขอข้อมูลตำแหน่ง ลองใหม่อีกครั้ง', 'error');
      break;
    default:
      showStatus('เกิดข้อผิดพลาดในการขอโลเคชั่น', 'error');
      break;
  }
  checkInButton.disabled = false;
}

function initMap() {
  if (!window.L) {
    showStatus('ไม่สามารถโหลดแผนที่ได้ ลองรีเฟรชหน้าใหม่', 'error');
    return;
  }

  map = L.map('map', {
    zoomControl: true,
    attributionControl: false
  }).setView([allowedLocation.lat, allowedLocation.lng], 15);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  campusMarker = L.marker([allowedLocation.lat, allowedLocation.lng]).addTo(map);
  campusMarker.bindPopup(`<strong>${allowedLocation.name}</strong><br>ระยะเช็คอินภายใน 1 กม.`).openPopup();

  campusCircle = L.circle([allowedLocation.lat, allowedLocation.lng], {
    radius: allowedLocation.radius,
    color: '#2563eb',
    fillColor: '#2563eb',
    fillOpacity: 0.12
  }).addTo(map);

  userMarker = L.marker([allowedLocation.lat, allowedLocation.lng], {
    opacity: 0.85
  }).addTo(map);
}

function updateUserMarker(lat, lng) {
  if (!map || !userMarker) return;
  userMarker.setLatLng([lat, lng]);
  userMarker.bindPopup(`ตำแหน่งของคุณ<br>ระยะห่าง ${Math.round(getDistanceMeters(lat, lng, allowedLocation.lat, allowedLocation.lng))} เมตร`).openPopup();
  const bounds = L.latLngBounds([
    [allowedLocation.lat, allowedLocation.lng],
    [lat, lng]
  ]).pad(0.2);
  map.fitBounds(bounds, { maxZoom: 15 });
}

function checkIn() {
  const name = studentNameInput.value.trim();
  if (!name) {
    showStatus('กรุณากรอกชื่อก่อนเช็คชื่อ', 'error');
    studentNameInput.focus();
    return;
  }

  if (!navigator.geolocation) {
    showStatus('เบราว์เซอร์นี้ไม่รองรับ Geolocation', 'error');
    return;
  }

  checkInButton.disabled = true;
  showStatus('กำลังตรวจสอบตำแหน่ง...', 'info');

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const { latitude, longitude } = position.coords;
      const distance = Math.round(getDistanceMeters(latitude, longitude, allowedLocation.lat, allowedLocation.lng));
      updateUserMarker(latitude, longitude);

      if (distance <= allowedLocation.radius) {
        showStatus(`เช็คอินสำเร็จ อยู่ในระยะ ${distance} เมตร`, 'info');
        addRecord(name, 'เช็คอินสำเร็จ', distance);
      } else {
        showStatus(`อยู่นอกพื้นที่เช็คอิน ${distance} เมตร ไม่สามารถเช็คอินได้`, 'error');
        addRecord(name, 'เช็คอินไม่สำเร็จ (เกิน 1 กม.)', distance);
      }
      checkInButton.disabled = false;
    },
    (error) => {
      handleLocationError(error);
      checkInButton.disabled = false;
    },
    {
      enableHighAccuracy: true,
      timeout: 20000,
      maximumAge: 0
    }
  );
}

function clearRecords() {
  if (confirm('ลบประวัติการเช็คชื่อทั้งหมดหรือไม่?')) {
    localStorage.removeItem(attendanceKey);
    renderRecords();
    showStatus('ล้างประวัติการเช็คชื่อเรียบร้อยแล้ว', 'info');
  }
}

checkInButton.addEventListener('click', checkIn);
clearRecordsButton.addEventListener('click', clearRecords);
initMap();
renderRecords();
