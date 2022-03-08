# Changelog

Note: for the latest "state" of the template spreadsheet, see [here](https://docs.google.com/spreadsheets/d/1BabID1n6fPgeuuO4-1r3mkoQ9Nx5dquNwdsET75In1E/edit#gid=288250820). This may be especially helpful when specifying environment variables.

### 2022-03-08
- **[feature]** Added "Flush Gradescope" functionality. Sometimes, extensions aren't properly applied to Gradescope, due to a variety of issues: invalid email/password combination, inaccurate due dates that are changed after-the-fact, assignment URL's that have been added after extensions have already been approved (e.g. for the case in which a student, at the beginning of the semester, requests an extension on all assignments), or some other Gradescope internal error. In these cases, we want a way to "flush" current extension state onto Gradescope. The updated [Google Apps Script Code](https://script.google.com/home/projects/10zaakwMYmDMs0hQu55PKzXlIC9jzGPGp7j1cQD028bhNHeBmJ1xa9WNJ/edit) adds a "Flush Gradescope" button to the drop-down menu. If you update your "Roster" sheet to have a `flush_gradescope` column (with data validation for all of that column's rows set to ["Checkboxes"](https://docs.google.com/spreadsheets/d/1BabID1n6fPgeuuO4-1r3mkoQ9Nx5dquNwdsET75In1E/edit#gid=1603800846)), then selecting "Actions" => "Flush Gradescope" will iteratively go through each selected student record, apply all of their extensions to Gradescope, and send a Slack message on job completi

### 2022-02-13
- **[feature]** Added support for an optional `hard_due_date` column on the Assignments tab for classes that want to specify a designated hard due date beyond which extensions for a particular assignment will not be granted. Approved extensions will be granted to the earlier of (original due date + # extension days, hard due date). If the hard due date is not set, when applying an extension to Gradescope, the hard due date will be updated to match the new assignment deadline.

### 2022-02-11
- **[feature]** Added support for optional `knows_assignments` form field (classes that don't want to support student support meetings through this system can delete all student support meeting related questions)
- **[feature]** Added support for optional `has_partner` form field (classes that don't have partner assignments at all can safely delete all form-related questions)
- **[feature]** Added support for optional `due_date` column on the Assignments tab (for classes that don't know all of their due dates ahead of time). If `due_date` is not specified, a warning will be displayed in Slack, but extensions may still be approved/auto-approved (students will recieve a TBD message in their email).

### 2022-02-10
- **[feature]** Added support for >= 2 partners. To enable this, change your form to specify that students working with partners can include a comma-separated list of names and SID's if they say they're working with a partner.

### 2022-02-07

- **[refactor]** Significantly refactored the internal base.
- **[fix]** Fixed a bug that was causing environment variables to be shared across classes (which was resulting in weird behavior with the `SLACK_TAG_LIST` environment variable specifically).
- **[feature]** Added support for Gradescope extensions. See the template for how to configure this feature.
- **[feature]** Added two optional columns to the Roster sheet: `last_run_output` and `last_run_timestamp` . If these are set, they will be auto-filled with helpful information from each run when new form submissions are processed.
- **[refactor]** Added signfiicant integration testing.

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
