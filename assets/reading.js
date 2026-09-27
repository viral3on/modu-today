const query = document.querySelector('#reading-query');
const cards = [...document.querySelectorAll('.post-card')];
const buttons = [...document.querySelectorAll('[data-filter]')];
const params = new URLSearchParams(location.search);
let category = params.get('category') || '';
query.value = params.get('q') || '';
function filter(updateURL=true) {
  const search = query.value.trim().toLowerCase();
  let count = 0;
  for (const card of cards) {
    card.hidden = Boolean(category && card.dataset.category !== category || search && !card.dataset.search.includes(search));
    if (!card.hidden) count++;
  }
  buttons.forEach(b=>b.setAttribute('aria-pressed', String(b.dataset.filter === category)));
  document.querySelector('#reading-count').textContent = `${count}개의 글`;
  document.querySelector('#no-results').hidden = count > 0 || !cards.length && !search && !category;
  const empty = document.querySelector('.post-grid > .empty-editorial');
  if (empty) empty.hidden = Boolean(search || category);
  if (updateURL) {
    const next = new URL(location.href); next.search = '';
    if (category) next.searchParams.set('category',category);
    if (search) next.searchParams.set('q',query.value.trim());
    history.replaceState(null,'',next);
  }
}
buttons.forEach(b=>b.addEventListener('click',()=>{category=b.dataset.filter;filter();}));
document.querySelector('form').addEventListener('submit',event=>{event.preventDefault();filter();});
query.addEventListener('input',()=>filter());
filter(false);
