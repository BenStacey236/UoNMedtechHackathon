document.addEventListener('DOMContentLoaded', function() {
  const button = document.getElementById('getHospitalsBtn');
  if (button) {
    button.addEventListener('click', function() {
      if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(function(position) {
          const data = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          };

          fetch('/nearest-hospitals', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
          })
          .then(response => response.json())
          .then(data => {
            if (data.error) {
              console.error('Error:', data.error);
            } else {
              displayHospitals(data.hospitals);
            }
          })
          .catch((error) => {
            console.error('Fetch error:', error);
          });
        }, function(error) {
          console.error('Geolocation error:', error);
        });
      } else {
        console.error('Geolocation is not supported by this browser.');
      }
    });
  } else {
    console.error('Button not found');
  }

  function displayHospitals(hospitals) {
    const hospitalsList = document.getElementById('hospitalsList');
    if (hospitalsList) {
      hospitalsList.innerHTML = '';
      hospitals.forEach(hospital => {
        const listItem = document.createElement('li');
        listItem.textContent = `${hospital.name} - ${hospital.address}`;
        hospitalsList.appendChild(listItem);
      });
    } else {
      console.error('Hospitals list container not found');
    }
  }
});
