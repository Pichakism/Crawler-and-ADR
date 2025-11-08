const express = require("express");
const router = express.Router();
const client = require("../elastic/client");
const jalaali = require("jalaali-js");

router.get("/", async (req, res) => {
  const { q, type, id, category, startDate, endDate } = req.query;

  try {
    let query = {};
    let suggestions = null;

    
    if (type === "id" && id) {
      
      query = { 
        bool: {
          should: [
            { term: { code: id.toString() } },
            { term: { id: parseInt(id) || 0 } }
          ]
        }
      };
    }
    
    else if (type === "title" && q) {
      query = { 
        match_phrase: { 
          title: { 
            query: q
          } 
        } 
      };
    }
    
    else if (type === "text" && q) {
      query = { 
        match_phrase: { 
          text: { 
            query: q
          } 
        } 
      };
    }
    
    else if (type === "summary" && q) {
      query = { 
        match_phrase: { 
          summary: { 
            query: q
          } 
        } 
      };
    }
    
    else if (type === "tags" && q) {
      query = { 
        match_phrase: { 
          tags: { 
            query: q
          } 
        } 
      };
    }
    
    else if (type === "category" && category) {
      query = { 
        match: { 
          category: { 
            query: category,
            operator: "and"
          } 
        } 
      };
    }
    
    else if (type === "date" && startDate && endDate) {
      query = {
        bool: {
          must: [
            { range: { date: { gte: startDate, lte: endDate } } }
          ]
        }
      };
      
      
      if (q) {
        query.bool.must.push({
          bool: {
            should: [
              { match_phrase: { title: { query: q } } },
              { match_phrase: { text: { query: q } } }
            ]
          }
        });
      }
    }
    
    else if (q) {
      query = {
        bool: {
          should: [
            { match_phrase: { title: { query: q } } },
            { match_phrase: { text: { query: q } } },
            { match_phrase: { category: { query: q } } }
          ]
        }
      };
    }
    else {
      return res.render("results", { 
        results: [], 
        query: "", 
        suggestions: null,
        error: "لطفا یک جستجو وارد کنید" 
      });
    }

    const result = await client.search({
      index: "news",
      body: { 
        query,
        highlight: q ? {
          fields: {
            title: { fragment_size: 150, number_of_fragments: 1 },
            summary: { fragment_size: 200, number_of_fragments: 1 },
            text: { fragment_size: 200, number_of_fragments: 2 },
            tags: { fragment_size: 100, number_of_fragments: 1 }
          }
        } : undefined,
        suggest: q ? {
          text_suggestion: {
            text: q,
            term: {
              field: "title",
              suggest_mode: "popular"
            }
          }
        } : undefined
      },
      size: 100
    });

    
    if (result.suggest && result.suggest.text_suggestion) {
      const suggestionsList = result.suggest.text_suggestion
        .flatMap(s => s.options.map(o => o.text))
        .filter((v, i, a) => a.indexOf(v) === i);
      
      if (suggestionsList.length > 0) {
        suggestions = suggestionsList;
      }
    }

    
    const resultsWithShamsiDate = result.hits.hits.map(hit => {
      const source = hit._source;
      if (source.date) {
        try {
          let dateStr = String(source.date);
          
          
          if (dateStr.includes('T') || dateStr.includes('-')) {
            
            const dateObj = new Date(dateStr);
            if (!isNaN(dateObj.getTime())) {
              const jDate = jalaali.toJalaali(dateObj);
              source.date_shamsi = `${jDate.jy}/${String(jDate.jm).padStart(2, '0')}/${String(jDate.jd).padStart(2, '0')}`;
            } else {
              source.date_shamsi = dateStr;
            }
          } else {
            
            const parts = dateStr.split('/');
            if (parts.length === 3) {
              const year = parseInt(parts[0]);
              if (year >= 1300 && year <= 1500) {
                
                source.date_shamsi = dateStr;
              } else {
                
                const gDate = new Date(year, parseInt(parts[1]) - 1, parseInt(parts[2]));
                if (!isNaN(gDate.getTime())) {
                  const jDate = jalaali.toJalaali(gDate);
                  source.date_shamsi = `${jDate.jy}/${String(jDate.jm).padStart(2, '0')}/${String(jDate.jd).padStart(2, '0')}`;
                } else {
                  source.date_shamsi = dateStr;
                }
              }
            } else {
              
              const dateObj = new Date(dateStr);
              if (!isNaN(dateObj.getTime())) {
                const jDate = jalaali.toJalaali(dateObj);
                source.date_shamsi = `${jDate.jy}/${String(jDate.jm).padStart(2, '0')}/${String(jDate.jd).padStart(2, '0')}`;
              } else {
                source.date_shamsi = dateStr;
              }
            }
          }
        } catch (e) {
          console.error(`[ERROR] خطا در تبدیل تاریخ ${source.date}:`, e.message);
          
          source.date_shamsi = source.date;
        }
      }
      return hit;
    });

    res.render("results", { 
      results: resultsWithShamsiDate, 
      query: q || id || category || "جستجو",
      suggestions,
      error: null,
      total: result.hits.total.value || result.hits.total
    });

  } catch (error) {
    console.error("خطا در جستجو:", error);
    res.render("results", { 
      results: [], 
      query: "",
      suggestions: null,
      error: "خطا در جستجو: " + error.message
    });
  }
});

module.exports = router;
