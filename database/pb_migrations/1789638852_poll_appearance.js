/// <reference path="../pb_data/types.d.ts" />
// Phase 7 poll themes: per-poll visual customization stored as JSON.
// Shape is validated server-side by PollAppearance (backend/app/schemas/poll.py).
// Older polls simply lack the field and render with the minimal theme.
migrate((db) => {
  const dao = new Dao(db);
  const polls = dao.findCollectionByNameOrId("polls");

  let hasField = false;
  for (let i = 0; i < polls.schema.length; i++) {
    if (polls.schema[i].name === "appearance") {
      hasField = true;
      break;
    }
  }
  if (!hasField) {
    polls.schema.addField(new SchemaField({
      name: "appearance",
      type: "json",
      required: false,
      options: {
        maxSize: 0
      }
    }));
    dao.saveCollection(polls);
  }
}, (db) => {
  const dao = new Dao(db);
  try {
    const polls = dao.findCollectionByNameOrId("polls");
    const field = polls.schema.getField
      ? polls.schema.getField("appearance")
      : polls.schema.find((f) => f.name === "appearance");
    if (field) {
      polls.schema.removeField(field.id);
      dao.saveCollection(polls);
    }
  } catch (e) {}
});
