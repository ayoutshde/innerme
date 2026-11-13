// The menu remains visible when JavaScript is unavailable.
document.documentElement.classList.add("js");
const menu = document.querySelector(".menu");
const navigation = document.querySelector("#primary-nav");
function setMenu(open) {
  menu.setAttribute("aria-expanded", String(open));
  navigation.classList.toggle("open", open);
}
menu.addEventListener("click", () => setMenu(menu.getAttribute("aria-expanded") !== "true"));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && menu.getAttribute("aria-expanded") === "true") {
    setMenu(false);
    menu.focus();
  }
});
// Quiz: choosing a circle submits the answer immediately.
const quizForm = document.querySelector(".quiz-form");
if (quizForm) {
  quizForm.querySelectorAll(".scale input").forEach((input) =>
    input.addEventListener("click", () => quizForm.requestSubmit())
  );
}