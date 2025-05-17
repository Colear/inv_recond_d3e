function myFunction() {
  btn = document.getElementById ('truc');
  console.log (btn.classList);
  if (btn.disabled == true) {
    btn.classList.remove('d-none');
    btn.disabled = false;
  }
  else {
    btn.classList.add('d-none');
    btn.disabled = true;  
  }
  console.log (btn.classList);
}

function DynForm() {
  var typeSelect = document.querySelector('select[name=type]')

  function hideFormElementsIfNotComputer() {
    var shouldHide = typeSelect.value !== 'tour'
    document.querySelectorAll('[name=cpu], [name=ram]')
      .forEach(function(element) {
        element.style.display = shouldHide ? 'none' : null
        element.disabled = shouldHide
        // this logging statement is just for showing what the example does
        console.log((shouldHide ? 'hide' : 'show'), 'element', element)
      })
  }
  typeSelect.addEventListener('change', hideFormElementsIfNotComputer)
  hideFormElementsIfNotComputer()
} 
