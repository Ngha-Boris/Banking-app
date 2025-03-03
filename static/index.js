// add event listener to submit event
function deposit() {
    var formData = new FormData(document.getElementById('deposit-form'));

    fetch('/deposit', {
        method: 'POST',
        body: formData
    })
    .then(response => response.text())
    .then(result => {
        document.getElementById('result').innerHTML = result;
    });
}


function withdraw() {
    var formData = new FormData(document.getElementById('withdraw-form'));

    fetch('/withdraw', {
        method: 'POST',
        body: formData
    })
    .then(response => response.text())
    .then(result => {
        document.getElementById('result').innerHTML = result;
    });
}