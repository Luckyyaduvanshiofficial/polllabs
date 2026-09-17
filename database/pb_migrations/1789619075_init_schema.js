/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db);
  const users = dao.findCollectionByNameOrId("users");

  // Enforce GitHub OAuth only on users collection per PRD §2
  users.options = {
    allowEmailAuth: false,
    allowOAuth2Auth: true,
    allowUsernameAuth: false,
    minPasswordLength: 8,
    requireEmail: false,
  };
  // Add deletion lifecycle fields to users collection per PRD §7
  users.schema.addField(new SchemaField({
    name: "deletion_status",
    type: "select",
    required: false,
    options: {
      maxSelect: 1,
      values: ["active", "pending_deletion"]
    }
  }));
  users.schema.addField(new SchemaField({
    name: "deletion_scheduled_for",
    type: "date",
    required: false
  }));
  dao.saveCollection(users);

  // 1. Create 'polls' collection
  const pollsCollection = new Collection({
    name: "polls",
    type: "base",
    system: false,
    schema: [
      {
        name: "title",
        type: "text",
        required: true,
        options: { min: 3, max: 200 }
      },
      {
        name: "description",
        type: "text",
        required: false,
        options: { max: 1000 }
      },
      {
        name: "options",
        type: "json",
        required: true
      },
      {
        name: "visibility",
        type: "select",
        required: true,
        options: {
          maxSelect: 1,
          values: ["public", "private"]
        }
      },
      {
        name: "result_display",
        type: "select",
        required: true,
        options: {
          maxSelect: 1,
          values: ["show_counts", "show_percentage", "hidden_until_close"]
        }
      },
      {
        name: "close_at",
        type: "date",
        required: false
      },
      {
        name: "owner",
        type: "relation",
        required: true,
        options: {
          collectionId: users.id,
          cascadeDelete: false,
          maxSelect: 1
        }
      },
      {
        name: "total_votes",
        type: "number",
        required: false,
        options: {
          min: 0
        }
      }
    ],
    indexes: [
      "CREATE INDEX idx_polls_visibility ON polls (visibility, created)",
      "CREATE INDEX idx_polls_owner ON polls (owner)"
    ],
    listRule: 'visibility = "public" || owner = @request.auth.id',
    viewRule: 'visibility = "public" || visibility = "private" || owner = @request.auth.id',
    createRule: '@request.auth.id != ""',
    updateRule: 'owner = @request.auth.id',
    deleteRule: 'owner = @request.auth.id'
  });

  dao.saveCollection(pollsCollection);

  // 2. Create 'votes' collection with cascadeDelete: true
  // createRule is null (locked) so votes MUST be submitted via FastAPI backend
  // which validates rate limits, IP hashes, and device tokens.
  const votesCollection = new Collection({
    name: "votes",
    type: "base",
    system: false,
    schema: [
      {
        name: "poll_id",
        type: "relation",
        required: true,
        options: {
          collectionId: pollsCollection.id,
          cascadeDelete: true,
          maxSelect: 1
        }
      },
      {
        name: "option_id",
        type: "text",
        required: true
      },
      {
        name: "device_token",
        type: "text",
        required: true
      },
      {
        name: "ip_hash",
        type: "text",
        required: true
      },
      {
        name: "embed_referrer",
        type: "text",
        required: false
      }
    ],
    indexes: [
      "CREATE INDEX idx_votes_poll ON votes (poll_id)",
      "CREATE INDEX idx_votes_device_poll ON votes (poll_id, device_token)",
      "CREATE INDEX idx_votes_ip_poll ON votes (poll_id, ip_hash)"
    ],
    listRule: null,
    viewRule: null,
    createRule: null,
    updateRule: null,
    deleteRule: null
  });

  dao.saveCollection(votesCollection);

  // 3. Create 'abuse_reports' collection with cascadeDelete: true
  const abuseReportsCollection = new Collection({
    name: "abuse_reports",
    type: "base",
    system: false,
    schema: [
      {
        name: "poll_id",
        type: "relation",
        required: true,
        options: {
          collectionId: pollsCollection.id,
          cascadeDelete: true,
          maxSelect: 1
        }
      },
      {
        name: "reason",
        type: "text",
        required: true,
        options: { min: 3, max: 1000 }
      },
      {
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
}, (db) => {
  const dao = new Dao(db);
  try {
    const abuse = dao.findCollectionByNameOrId("abuse_reports");
    if (abuse) dao.deleteCollection(abuse);
  } catch (e) {}

  try {
    const votes = dao.findCollectionByNameOrId("votes");
    if (votes) dao.deleteCollection(votes);
  } catch (e) {}

  try {
    const polls = dao.findCollectionByNameOrId("polls");
    if (polls) dao.deleteCollection(polls);
  } catch (e) {}
});
