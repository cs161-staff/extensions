# Changelog

Note: for the latest "state" of the template spreadsheet, see [here](https://docs.google.com/spreadsheets/d/1BabID1n6fPgeuuO4-1r3mkoQ9Nx5dquNwdsET75In1E/edit#gid=288250820). This may be especially helpful when specifying environment variables.

### 2022-01-31

- **[update]** Slightly tweaked the wording of Slack messages to make them more approval-friendly  ("An extension request needs review" vs. "An extension request could not be auto-approved").

### 2022-01-30

- **[feature]** It's no longer necessary to add all students to your `Roster` sheet ahead of time. We recieved feedback that it's difficult to keep the roster updated through adds/drops/swaps/etc., so we migrated to an on-demand model, where students are inserted into the roster only when they submit an extension request. If they submit multiple, their existing roster entry is updated in-place.

- **[update]** Student names are no longer used in sending emails (we start emails with "Hi," instead of "Hi [name],"). We recieved feedback that many students' official names aren't the names that they go by, so we migrated to a more general email greeting. This effectively makes the `name` column on the `Roster` optional.

### 2022-01-29

- **[feature]** If a `last_updated` column is present on the `Roster` sheet, this tool will write the current timestamp to that column for row that it modifies in extension processing. This is useful when processing extensions manually (just sort by the `last_updated` column). Feel free to add this column to the `Roster`, and the tool will automatically detect it and start using it.
- **[feature]** Retroactive extensions (extensions requested after an assignment is due) are now flagged for human review.

### 2022-01-28

- **[feature]** Feel free to add a `SLACK_TAG_LIST` environment variable, with zero or more comma-separated lists of users who you'd like to tag in Slack messages that require manual approval. This is helpful in classes that have many auto-approvals (e.g. you can see all action-related items chronologically in your Slack `Mentions and Reactions`).
- **[update]** Emails (instead of SID's) are now used to look up students & partners on the roster. We recommend keeping the SID field on your form as a fallback, just in case the student's email is not found. This effectively makes the `sid` column on the `Roster` optional.
- **[migration]** The migration from SendGrid to CS 162's mailserver is complete. The `SENDGRID_API_KEY` environment variable is no longer needed. You may want to reformat your `EMAIL_FROM` address to be in the form of `Sender Name <senderemail@berkeley.edu>`, so that email clients recognize and use the sender name. Note that your sender email can be any @berkeley.edu email.

### 2022-01-27

- **[fix]** We noticed that the Form Template that we released to some classes had incorrect regex validation for the "# of Days" question. To fix this issue, on your form, for the validation of that question's input, set it to "Regular expression matches `\d+(,\d+)*`".
