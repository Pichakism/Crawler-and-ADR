const express = require("express");
const path = require("path");
const app = express();
const port = 3000;
const searchRoute = require("./routes/search");

// EJS settings
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));

// Static files
app.use(express.static(path.join(__dirname, "public")));

// Home page
app.get("/", (req, res) => {
  res.render("index", { title: "News Search" });
});

app.use("/search", searchRoute);

// Start the server
app.listen(port, () => console.log("Server running on http://localhost:" + port));
