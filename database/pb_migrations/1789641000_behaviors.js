/// <reference path="../pb_data/pb_hooks/index.d.ts" />

/**
 * Phase 5: Behaviors — multi-select, quiz mode, visible voters.
 *
 * Adds poll-level config fields and stores multi-option votes
 * as JSON arrays in the existing option_id column.
 */
migrate((app) => {
  const polls = app.findCollectionByNameOrId("polls");

  // --- max_selections (int, default 1) ---
  if (!polls.getField("max_selections")) {
    polls.addField(new Field({
      name: "max_selections",
      type: "number",
      required: false,
      system: false,
      options: { min: 1, max: 10 },
    }));
  }

  // --- is_quiz (bool, default false) ---
  if (!polls.getField("is_quiz")) {
    polls.addField(new Field({
      name: "is_quiz",
      type: "bool",
      required: false,
      system: false,
    }));
  }

  // --- correct_options (json, optional) ---
  if (!polls.getField("correct_options")) {
    polls.addField(new Field({
      name: "correct_options",
      type: "json",
      required: false,
      system: false,
      options: { maxSize: 2000 },
    }));
  }

  // --- show_voters (bool, default false) ---
  if (!polls.getField("show_voters")) {
    polls.addField(new Field({
      name: "show_voters",
      type: "bool",
      required: false,
      system: false,
    }));
  }

  app.save(polls);

  // --- Migrate votes.option_id from string to JSON (supports arrays) ---
  const votes = app.findCollectionByNameOrId("votes");
  const optionField = votes.getField("option_id");
  if (optionField && optionField.type !== "json") {
    votes.removeField("option_id");
    votes.addField(new Field({
      name: "option_id",
      type: "json",
      required: true,
      system: false,
      options: { maxSize: 0 },
    }));
    app.save(votes);
  }
}, "1789641000_behaviors");
