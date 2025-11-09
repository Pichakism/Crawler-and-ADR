
const crawlBtn = document.getElementById("crawlBtn");
const searchBtn = document.getElementById("searchBtn");
const crawlBox = document.getElementById("crawlBox");
const searchBox = document.getElementById("searchBox");

crawlBtn.addEventListener("click", () => {
  crawlBox.style.display = "block";
  searchBox.style.display = "none";
  crawlBtn.classList.add("active");
  searchBtn.classList.remove("active");
});

searchBtn.addEventListener("click", () => {
  crawlBox.style.display = "none";
  searchBox.style.display = "block";
  crawlBtn.classList.remove("active");
  searchBtn.classList.add("active");
});

document.addEventListener("DOMContentLoaded", () => {
  
  
  if (sessionStorage.getItem('showSearchTab') === 'true') {
    sessionStorage.removeItem('showSearchTab');
    
    crawlBox.style.display = "none";
    searchBox.style.display = "block";
    crawlBtn.classList.remove("active");
    searchBtn.classList.add("active");
  }
  
  
  const items = document.querySelectorAll(".accordion .item");
  items.forEach((item) => {
    const title = item.querySelector(".title");
    const content = item.querySelector(".content");

    title.addEventListener("click", () => {
      const isOpen = content.classList.contains("open");
      document.querySelectorAll(".accordion .content").forEach((c) => {
        c.classList.remove("open");
        c.style.maxHeight = null;
      });

      if (!isOpen) {
        content.classList.add("open");
        content.style.maxHeight = content.scrollHeight + 15 + "px";
      }
    });
  });

  
  if (window.jQuery) {
    $("#fromDate, #toDate, #searchFrom, #searchTo").persianDatepicker({
      format: "YYYY/MM/DD",
      autoClose: true,
      initialValue: false,
      calendar: {
        persian: {
          locale: 'fa'
        }
      },
      observer: true,
      altField: false
    });
  }

  
  document.querySelector("#crawlBox button").addEventListener("click", async () => {
    const startDate = document.getElementById("fromDate").value;
    const endDate = document.getElementById("toDate").value;

    if (!startDate || !endDate) {
      alert("لطفا تاریخ شروع و پایان را وارد کنید");
      return;
    }

    const btn = document.querySelector("#crawlBox button");
    btn.textContent = "در حال استخراج...";
    btn.disabled = true;

    try {
      const response = await fetch("/crawl", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ startDate, endDate })
      });

      const result = await response.json();
      
      if (result.success) {
        alert(`✅ ${result.message}`);
      } else {
        alert("❌ خطا: " + result.error);
      }
    } catch (error) {
      alert("❌ خطا در ارتباط با سرور: " + error.message);
    } finally {
      btn.textContent = "استخراج";
      btn.disabled = false;
    }
  });

  
  document.querySelector("#titleSearch button").addEventListener("click", () => {
    const query = document.querySelector("#titleSearch input").value;
    if (!query) {
      alert("لطفا عبارت جستجو را وارد کنید");
      return;
    }
    window.location.href = `/search?type=title&q=${encodeURIComponent(query)}`;
  });

  
  document.querySelector("#textSearch button").addEventListener("click", () => {
    const query = document.querySelector("#textSearch input").value;
    if (!query) {
      alert("لطفا عبارت جستجو را وارد کنید");
      return;
    }
    window.location.href = `/search?type=text&q=${encodeURIComponent(query)}`;
  });

  
  document.querySelector("#summarySearch button").addEventListener("click", () => {
    const query = document.querySelector("#summarySearch input").value;
    if (!query) {
      alert("لطفا عبارت جستجو را وارد کنید");
      return;
    }
    window.location.href = `/search?type=summary&q=${encodeURIComponent(query)}`;
  });

  
  document.querySelector("#tagsSearch button").addEventListener("click", () => {
    const query = document.querySelector("#tagsSearch input").value;
    if (!query) {
      alert("لطفا عبارت جستجو را وارد کنید");
      return;
    }
    window.location.href = `/search?type=tags&q=${encodeURIComponent(query)}`;
  });

  
  document.querySelector("#idSearch button").addEventListener("click", () => {
    const newsId = document.querySelector("#idSearch input").value;
    if (!newsId) {
      alert("لطفا شماره خبر را وارد کنید");
      return;
    }
    window.location.href = `/search?type=id&id=${encodeURIComponent(newsId)}`;
  });

  
  document.querySelector("#categorySearch button").addEventListener("click", () => {
    const category = document.querySelector("#categorySearch input").value;
    if (!category) {
      alert("لطفا موضوع خبر را وارد کنید");
      return;
    }
    window.location.href = `/search?type=category&category=${encodeURIComponent(category)}`;
  });

});
