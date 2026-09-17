/// <reference path="../pb_data/types.d.ts" />
// Adds what 1789619075_init_schema.js gained AFTER it was already applied:
//  - users.deletion_status + users.deletion_scheduled_for (PRD §7)
//  - abuse_reports collection with cascadeDelete + locked API rules (PRD §4.6)
// Live DB at 90acd14b had polls/users/votes only; pb_schema.json already
// describes all four collections, so this migration converges live DB to schema.
migrate((db) => {
  const dao = new Dao(db);

  // 1. Users deletion lifecycle fields (skip if already present)
  const users = dao.findCollectionByNameOrId("users");
  const hasField = (name) => {
    let found = false;
    for (let i = 0; i < users.schema.length; i++) {
      if (users.schema[i].name === name) {
        found = true;
        break;
      }
    }
    return found;
  };
  if (!hasField("deletion_status")) {
    users.schema.addField(new SchemaField({
      id: "users_deletion_status",
      name: "deletion_status",
      type: "select",
      required: false,
      options: {
        maxSelect: 1,
        values: ["active", "pending_deletion"]
      }
    }));
  }
  if (!hasField("deletion_scheduled_for")) {
    users.schema.addField(new SchemaField({
      id: "users_deletion_sched",
      name: "deletion_scheduled_for",
      type: "date",
      required: false
    }));
  }
  dao.saveCollection(users);

  // 2. Create 'abuse_reports' collection (skip if it already exists)
  let abuseExists = true;
  try {
    dao.findCollectionByNameOrId("abuse_reports");
  } catch (e) {
    abuseExists = false;
  }
  if (!abuseExists) {
    const polls = dao.findCollectionByNameOrId("polls");
    const abuseReportsCollection = new Collection({
      id: "71mbs71bjj9fvab",
      name: "abuse_reports",
      type: "base",
      system: false,
      schema: [
        {
          id: "7nbxsxla",
          name: "poll_id",
          type: "relation",
          required: true,
          options: {
            collectionId: polls.id,
            cascadeDelete: true,
            maxSelect: 1
          }
        },
        {
          id: "7uv7axyw",
          name: "reason",
          type: "text",
          required: true,
          options: { min: 3, max: 1000 }
        },
        {
          id: "7xuxaq9s",
          name: "ip_hash",
          type: "text",
          required: true
        }
      ],
      indexes: [
        "CREATE INDEX idx_abuse_poll ON abuse_reports (poll_id)"
      ],
      listRule: null,
      viewRule: null,
      createRule: null,
      updateRule: null,
      deleteRule: null
    });

    dao.saveCollection(abuseReportsCollection);
  }
}, (db) => {
  const dao = new Dao(db);
  try {
    const abuse = dao.findCollectionByNameOrId("abuse_reports");
    if (abuse) dao.deleteCollection(abuse);
  } catch (e) {}

  try {
    const users = dao.findCollectionByNameOrId("users");
    try { users.schema.removeField("users_deletion_sched"); } catch (e) {}
    try { users.schema.removeField("users_deletion_status"); } catch (e) {}
    dao.saveCollection(users);
  } catch (e) {}
});
