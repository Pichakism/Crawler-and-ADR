// === بخش جدید: کنترل تب‌های کارت مرکزی ===
const crawlBtn = document.getElementById("crawlBtn");
const searchBtn = document.getElementById("searchBtn");
const crawlBox = document.getElementById("crawlBox");
const searchBox = document.getElementById("searchBox");

crawlBtn.addEventListener("click", () => {
  // نمایش محتوای استخراج
  crawlBox.style.display = "block";
  searchBox.style.display = "none";
  
  // فعال کردن تب
  crawlBtn.classList.add("active");
  searchBtn.classList.remove("active");
});

searchBtn.addEventListener("click", () => {
  // نمایش محتوای جستجو
  crawlBox.style.display = "none";
  searchBox.style.display = "block";

  // فعال کردن تب
  crawlBtn.classList.remove("active");
  searchBtn.classList.add("active");
});


// === بخش قبلی: کدهای داخل DOMContentLoaded (بدون تغییر) ===
// وقتی کل صفحه لود شد
document.addEventListener("DOMContentLoaded", () => {
  
  // ✅ آکاردئون جستجوی اخبار
  const items = document.querySelectorAll(".accordion .item");

  items.forEach((item) => {
    const title = item.querySelector(".title");
    const content = item.querySelector(".content");

    title.addEventListener("click", () => {
      const isOpen = content.classList.contains("open");

      // بستن همه‌ی آکاردئون‌ها
      document.querySelectorAll(".accordion .content").forEach((c) => {
        c.classList.remove("open");
        c.style.maxHeight = null;
      });

      // باز کردن همونی که روش کلیک شده
      if (!isOpen) {
        content.classList.add("open");
        content.style.maxHeight = content.scrollHeight + "px";
      }
    });
  });

  // ✅ فعال‌سازی تقویم شمسی
  if (window.jQuery) {
    $("#fromDate, #toDate, #searchFrom, #searchTo").persianDatepicker({
      format: "YYYY/MM/DD",
      autoClose: true,
      initialValueType: "gregorian"
    });
  }

  // ✅ اصلاح رفتار دکمه‌های داخلی (برای جلوگیری از تداخل با آکاردئون)
  document.querySelectorAll(".accordion .content button").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      console.log("🔍 دکمه جستجو کلیک شد:", btn.parentElement.id);
    });
  });
});