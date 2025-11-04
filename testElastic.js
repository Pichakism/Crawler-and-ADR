const client = require('./elastic/client');

(async () => {
  try {
    const info = await client.info();
    console.log("✅ Connected to Elasticsearch:");
    console.log(info);
  } catch (err) {
    console.error("❌ Connection failed:", err);
  }
})();
