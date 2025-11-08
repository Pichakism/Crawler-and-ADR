const express = require("express");
const path = require("path");
const app = express();
const port = 3000;
const searchRoute = require("./routes/search");
const crawlRoute = require("./routes/crawl");


app.use(express.json());
app.use(express.urlencoded({ extended: true }));


app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));


app.use(express.static(path.join(__dirname, "public")));


app.get("/", (req, res) => {
  res.render("index", { title: "News Search" });
});

app.use("/search", searchRoute);
app.use("/crawl", crawlRoute);


app.listen(port, () => console.log("Server running on http://localhost:" + port));
