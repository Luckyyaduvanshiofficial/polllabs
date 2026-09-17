/// <reference path="../pb_data/types.d.ts" />
// Retry of 1789639466 (in-place options mutation did not persist).
// Replaces the two JSON fields with identical definitions except maxSize,
// so polls (options) and Phase 7 themes (appearance) can actually be stored.
// polls table is empty in every environment at this point, so no data moves.
migrate((db) => {
  const dao = new Dao(db);
  const polls = dao.findCollectionByNameOrId("polls");

  const replace = (oldId, def) => {
    try {
      polls.schema.removeField(oldId);
    } catch (e) {}
    polls.schema.addField(new SchemaField(def));
  };

  replace("yov5vvgk", {
    id: "yov5vvgk",
    name: "options",
    type: "json",
    required: true,
    options: { maxSize: 20000 },
  });
  replace("ugvszf94", {
    id: "ugvszf94",
    name: "appearance",
    type: "json",
    required: false,
    options: { maxSize: 5000 },
  });

  dao.saveCollection(polls);
}, (db) => {
  const dao = new Dao(db);
  try {
    const polls = dao.findCollectionByNameOrId("polls");
    try {
      polls.schema.removeField("yov5vvgk");
    } catch (e) {}
    polls.schema.addField(new SchemaField({
      id: "yov5vvgk",
      name: "options",
      type: "json",
      required: true,
      options: { maxSize: 0 },
    }));
    try {
      polls.schema.removeField("ugvszf94");
    } catch (e) {}
    polls.schema.addField(new SchemaField({
      id: "ugvszf94",
      name: "appearance",
      type: "json",
      required: false,
      options: { maxSize: 0 },
    }));
    dao.saveCollection(polls);
  } catch (e) {}
});
