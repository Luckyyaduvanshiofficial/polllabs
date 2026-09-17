/// <reference path="../pb_data/types.d.ts" />
// JSON fields created without maxSize default to a 0-byte limit, which
// rejects every write ("validation_json_size_limit"). Set real limits so
// polls (options) and Phase 7 themes (appearance) can actually be stored.
migrate((db) => {
  const dao = new Dao(db);
  const polls = dao.findCollectionByNameOrId("polls");

  for (let i = 0; i < polls.schema.length; i++) {
    const f = polls.schema[i];
    if (f.name === "options") {
      f.options.maxSize = 20000;
    }
    if (f.name === "appearance") {
      f.options.maxSize = 5000;
    }
  }
  dao.saveCollection(polls);
}, (db) => {
  const dao = new Dao(db);
  try {
    const polls = dao.findCollectionByNameOrId("polls");
    for (let i = 0; i < polls.schema.length; i++) {
      const f = polls.schema[i];
      if (f.name === "options" || f.name === "appearance") {
        f.options.maxSize = 0;
      }
    }
    dao.saveCollection(polls);
  } catch (e) {}
});
