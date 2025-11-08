// === New section: control tabs in the central card ===
const crawlBtn = document.getElementById("crawlBtn");
const searchBtn = document.getElementById("searchBtn");
const crawlBox = document.getElementById("crawlBox");
const searchBox = document.getElementById("searchBox");

crawlBtn.addEventListener("click", () => {
  // Show the crawling content
  crawlBox.style.display = "block";
  searchBox.style.display = "none";
  
  // Activate the tab
  crawlBtn.classList.add("active");
  searchBtn.classList.remove("active");
});

searchBtn.addEventListener("click", () => {
  // Show the search content
  crawlBox.style.display = "none";
  searchBox.style.display = "block";

  // Activate the tab
  crawlBtn.classList.remove("active");
  searchBtn.classList.add("active");
});


// === Previous section: code inside DOMContentLoaded (unchanged) ===
// When the entire page has loaded
document.addEventListener("DOMContentLoaded", () => {
  
  //News search accordion
  const items = document.querySelectorAll(".accordion .item");

  items.forEach((item) => {
    const title = item.querySelector(".title");
    const content = item.querySelector(".content");

    title.addEventListener("click", () => {
      const isOpen = content.classList.contains("open");

      //Close all accordion sections
      document.querySelectorAll(".accordion .content").forEach((c) => {
        c.classList.remove("open");
        c.style.maxHeight = null;
      });

      // Open the one that was clicked
      if (!isOpen) {
        content.classList.add("open");
        content.style.maxHeight = content.scrollHeight + "px";
      }
    });
  });

  //Initialize Persian calendar
  if (window.jQuery) {
    $("#fromDate, #toDate, #searchFrom, #searchTo").persianDatepicker({
      format: "YYYY/MM/DD",
      autoClose: true,
      initialValueType: "gregorian"
    });
  }

  //Fix behavior of inner buttons (prevent conflict with accordion)
  document.querySelectorAll(".accordion .content button").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      console.log("🔍 Search button clicked:", btn.parentElement.id);
    });
  });
});
