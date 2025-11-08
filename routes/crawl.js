const express = require("express");
const router = express.Router();
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs").promises;
const client = require("../elastic/client");
const jalaali = require("jalaali-js");


function persianToEnglishNumbers(str) {
  if (!str) return str;
  const persianDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
  const englishDigits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
  
  let result = str.toString();
  for (let i = 0; i < 10; i++) {
    result = result.replace(new RegExp(persianDigits[i], 'g'), englishDigits[i]);
  }
  return result;
}


function persianToGregorian(persianDate) {
  try {
    
    persianDate = persianToEnglishNumbers(persianDate);
    
    
    const parts = persianDate.split('/');
    if (parts.length !== 3) return persianDate;
    
    const jYear = parseInt(parts[0]);
    const jMonth = parseInt(parts[1]);
    const jDay = parseInt(parts[2]);
    
    if (isNaN(jYear) || isNaN(jMonth) || isNaN(jDay)) return persianDate;
    
    
    if (jYear < 1300 || jYear > 1500) {
      return persianDate;
    }
    
    
    const gregorian = jalaali.toGregorian(jYear, jMonth, jDay);
    
    return `${gregorian.gy}/${String(gregorian.gm).padStart(2, '0')}/${String(gregorian.gd).padStart(2, '0')}`;
  } catch (error) {
    console.error(`[ERROR] خطا در تبدیل تاریخ ${persianDate}:`, error.message);
    return persianDate;
  }
}

router.post("/", async (req, res) => {
  let { startDate, endDate } = req.body;
  
  if (!startDate || !endDate) {
    return res.status(400).json({ error: "تاریخ شروع و پایان الزامی است" });
  }

  
  startDate = persianToEnglishNumbers(startDate);
  endDate = persianToEnglishNumbers(endDate);
  
  console.log(`[INFO] تاریخ شمسی دریافت شده - شروع: ${startDate}, پایان: ${endDate}`);
  
  
  

  try {
    
    const pythonScript = path.join(__dirname, "../crawler/crawler.py");
    const python = spawn("python", [pythonScript, startDate, endDate]);

    let output = "";
    let errorOutput = "";

    python.stdout.on("data", (data) => {
      output += data.toString();
      console.log(data.toString());
    });

    python.stderr.on("data", (data) => {
      errorOutput += data.toString();
      console.error(data.toString());
    });

    python.on("close", async (code) => {
      console.log("Python process exited with code:", code);
      console.log("Output:", output);
      console.log("Error output:", errorOutput);

      if (code !== 0) {
        return res.status(500).json({ 
          error: "خطا در کراول", 
          details: errorOutput || output || "خطای نامشخص در اجرای کراولر Python"
        });
      }

      try {
        
        const newsFile = path.join(__dirname, "../news_data/all_news.json");
        
        
        try {
          await fs.access(newsFile);
        } catch (err) {
          return res.status(500).json({ 
            error: "فایل اخبار پیدا نشد", 
            details: "کراولر فایل all_news.json را ایجاد نکرده است. لطفا لاگ‌های Python را بررسی کنید."
          });
        }

        const newsData = await fs.readFile(newsFile, "utf-8");
        const news = JSON.parse(newsData);

        if (!Array.isArray(news) || news.length === 0) {
          return res.status(200).json({ 
            success: true, 
            message: "هیچ خبری در بازه زمانی انتخابی پیدا نشد",
            count: 0 
          });
        }

        
        await indexNewsToElastic(news);

        res.json({ 
          success: true, 
          message: `${news.length} خبر با موفقیت کراول و ایندکس شد`,
          count: news.length 
        });
      } catch (err) {
        console.error("Error processing news:", err);
        res.status(500).json({ 
          error: "خطا در پردازش اخبار", 
          details: err.message 
        });
      }
    });
  } catch (error) {
    res.status(500).json({ error: "خطای سرور", details: error.message });
  }
});

async function indexNewsToElastic(newsArray) {
  
  const indexExists = await client.indices.exists({ index: "news" });
  
  if (!indexExists) {
    await client.indices.create({
      index: "news",
      body: {
        settings: {
          analysis: {
            analyzer: {
              persian_analyzer: {
                type: "custom",
                tokenizer: "standard",
                char_filter: ["persian_normalize"],
                filter: [
                  "lowercase",
                  "persian_stop"
                ]
              }
            },
            char_filter: {
              persian_normalize: {
                type: "mapping",
                mappings: [
                  "ا => آ",  
                  "ي => ی",  
                  "ك => ک",  
                  "ة => ه",  
                  "ئ => ی",  
                  "ؤ => و",  
                  "أ => آ",  
                  "إ => ا",  
                  "ٱ => ا"   
                ]
              }
            },
            filter: {
              persian_stop: {
                type: "stop",
                stopwords: ["و", "در", "به", "از", "که", "این", "آن", "با", "برای", "تا", "را", "است", "بود", "شد", "می", "های"]
              }
            }
          }
        },
        mappings: {
          properties: {
            id: { type: "integer" },
            code: { type: "keyword" },  
            title: { type: "text", analyzer: "persian_analyzer" },
            summary: { type: "text", analyzer: "persian_analyzer" },  
            text: { type: "text", analyzer: "persian_analyzer" },
            category: { type: "text", analyzer: "persian_analyzer" },  
            date: { type: "date", format: "yyyy/MM/dd" },
            time: { type: "keyword" },
            url: { type: "keyword" },
            short_url: { type: "keyword" },  
            tags: { type: "text", analyzer: "persian_analyzer" }  
          }
        }
      }
    });
  } else {
    
    console.log("[INFO] در حال پاک کردن اخبار قبلی...");
    try {
      await client.deleteByQuery({
        index: "news",
        body: {
          query: {
            match_all: {}
          }
        },
        refresh: true
      });
      console.log("[OK] اخبار قبلی پاک شد");
    } catch (error) {
      console.error("[ERROR] خطا در پاک کردن اخبار قبلی:", error.message);
      
      try {
        await client.indices.delete({ index: "news" });
        console.log("[INFO] ایندکس قدیمی پاک شد، در حال ساخت مجدد...");
        await client.indices.create({
          index: "news",
          body: {
            settings: {
              analysis: {
                analyzer: {
                  persian_analyzer: {
                    type: "custom",
                    tokenizer: "standard",
                    char_filter: ["persian_normalize"],
                    filter: [
                      "lowercase",
                      "persian_stop"
                    ]
                  }
                },
                char_filter: {
                  persian_normalize: {
                    type: "mapping",
                    mappings: [
                      "ا => آ",
                      "ي => ی",
                      "ك => ک",
                      "ة => ه",
                      "ئ => ی",
                      "ؤ => و",
                      "أ => آ",
                      "إ => ا",
                      "ٱ => ا"
                    ]
                  }
                },
                filter: {
                  persian_stop: {
                    type: "stop",
                    stopwords: ["و", "در", "به", "از", "که", "این", "آن", "با", "برای", "تا", "را", "است", "بود", "شد", "می", "های"]
                  }
                }
              }
            },
            mappings: {
              properties: {
                id: { type: "integer" },
                code: { type: "keyword" },
                title: { type: "text", analyzer: "persian_analyzer" },
                summary: { type: "text", analyzer: "persian_analyzer" },
                text: { type: "text", analyzer: "persian_analyzer" },
                category: { type: "text", analyzer: "persian_analyzer" },
                date: { type: "date", format: "yyyy/MM/dd" },
                time: { type: "keyword" },
                url: { type: "keyword" },
                short_url: { type: "keyword" },
                tags: { type: "text", analyzer: "persian_analyzer" }
              }
            }
          }
        });
        console.log("[OK] ایندکس جدید ساخته شد");
      } catch (deleteError) {
        console.error("[ERROR] خطا در پاک و ساخت مجدد ایندکس:", deleteError.message);
        throw deleteError;
      }
    }
  }

  
  for (const news of newsArray) {
    
    let cleanedNews = { ...news };
    
    if (cleanedNews.date) {
      
      cleanedNews.date = persianToEnglishNumbers(cleanedNews.date);
      
      
      const dateYear = parseInt(cleanedNews.date.split('/')[0]);
      if (dateYear >= 1300 && dateYear <= 1500) {
        cleanedNews.date = persianToGregorian(cleanedNews.date);
        console.log(`[INFO] تاریخ خبر ${news.id} تبدیل شد: ${news.date} -> ${cleanedNews.date}`);
      }
    }
    
    await client.index({
      index: "news",
      id: cleanedNews.id.toString(),
      document: cleanedNews
    });
  }

  await client.indices.refresh({ index: "news" });
  console.log(`✅ ${newsArray.length} خبر در Elasticsearch ایندکس شد`);
}

module.exports = router;

