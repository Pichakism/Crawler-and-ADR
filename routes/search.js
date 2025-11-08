const express = require("express");
const router = express.Router();
const client = require("../elastic/client");

router.get("/", async (req, res) => {
  const query = req.query.q || "";
  const { hits } = await client.search({
    index: "news",
    query: {
      match: { title: query }
    }
  });

  res.render("results", { results: hits.hits });
});

module.exports = router;
