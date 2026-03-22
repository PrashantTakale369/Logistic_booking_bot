/* LogiBot — Landing Page JS */

function swapCities() {
    var fc = document.getElementById('from_city');
    var tc = document.getElementById('to_city');
    var fa = document.getElementById('from_addr');
    var ta = document.getElementById('to_addr');
    var tmp1 = fc.value; fc.value = tc.value; tc.value = tmp1;
    var tmp2 = fa.value; fa.value = ta.value; ta.value = tmp2;
}

function selectChip(el) {
    var chips = document.querySelectorAll('.chip');
    for (var i = 0; i < chips.length; i++) chips[i].classList.remove('on');
    el.classList.add('on');
}

function submitBooking() {
    var data = {
        submitted:      '1',
        from_city:      document.getElementById('from_city').value || '',
        from_address:   document.getElementById('from_addr').value || '',
        to_city:        document.getElementById('to_city').value || '',
        to_address:     document.getElementById('to_addr').value || '',
        pickup_date:    document.getElementById('pickup_date').value,
        service_type:   document.getElementById('service').value,
        transport_mode: document.getElementById('transport').value,
        num_packages:   document.getElementById('packages').value,
        weight:         document.getElementById('weight').value
    };

    /* Create a hidden form targeting _top to escape the iframe sandbox */
    var form = document.createElement('form');
    form.method = 'GET';
    form.target = '_top';
    form.action = '/';

    Object.keys(data).forEach(function(key) {
        var input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = data[key];
        form.appendChild(input);
    });

    document.body.appendChild(form);
    form.submit();
}
