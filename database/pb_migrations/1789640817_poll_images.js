/// <reference path="../pb_data/types.d.ts" />
// Phase 4: poll_images collection for YouTube-style thumbnail options.
// Files are uploaded ONLY via the FastAPI backend (locked null API rules,
// admin token), which validates mime + size before forwarding to PocketBase.
// poll_id is optional so images can be staged before the poll is published;
// orphan rows (empty poll_id, older than 24h) are cleaned opportunistically
// by the upload endpoint. Storage backend (local or S3) is transparent:
// files are always served via /api/files/... URLs.
migrate((db) => {
  const dao = new Dao(db);

  let exists = true;
  try {
    dao.findCollectionByNameOrId("poll_images");
  } catch (e) {
    exists = false;
  }
  if (exists) return;

  const polls = dao.findCollectionByNameOrId("polls");
  const users = dao.findCollectionByNameOrId("users");

  const imagesCollection = new Collection({
    name: "poll_images",
    type: "base",
    system: false,
    schema: [
      {
        name: "poll_id",
        type: "relation",
        required: false,
        options: {
          collectionId: polls.id,
          cascadeDelete: true,
          maxSelect: 1,
        },
      },
      {
        name: "owner",
        type: "relation",
        required: true,
        options: {
          collectionId: users.id,
          cascadeDelete: true,
          maxSelect: 1,
        },
      },
      {
        name: "image",
        type: "file",
        required: true,
        options: {
          mimeTypes: [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
          ],
          maxSelect: 1,
          maxSize: 5242880,
        },
      },
    ],
    indexes: [
      "CREATE INDEX idx_images_poll ON poll_images (poll_id)",
      "CREATE INDEX idx_images_owner ON poll_images (owner)",
    ],
    listRule: null,
    viewRule: null,
    createRule: null,
    updateRule: null,
    deleteRule: null,
  });

  dao.saveCollection(imagesCollection);
}, (db) => {
  const dao = new Dao(db);
  try {
    const images = dao.findCollectionByNameOrId("poll_images");
    if (images) dao.deleteCollection(images);
  } catch (e) {}
});
