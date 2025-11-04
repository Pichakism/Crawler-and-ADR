const express = require("express");
const path = require("path");
const app = express();
const port = 3000;
const searchRoute = require("./routes/search");


// تنظیمات EJS
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));

// فایل‌های استاتیک
app.use(express.static(path.join(__dirname, "public")));

// صفحه اصلی
app.get("/", (req, res) => {
  res.render("index", { title: "News Search" });
});


app.use("/search", searchRoute);


// شروع سرور
app.listen(port, () => console.log("Server running on http://localhost:" + port));
