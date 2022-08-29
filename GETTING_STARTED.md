# Getting Started

If you'd like us to walk you through setup, feel free to email fuzailshakir@berkeley.edu or join the `#161-extension-bot` channel on EECS Crossroads. That said, all of this is self-serve, so you could follow this guide entirely by yourself if you'd like!

It takes ~15 minutes to onboard your class onto this tool, and that time pays off as soon as your first extension requests start rolling in :)

### Part 1: Configuring Slack

_Estimated Time: 5 minutes_

You'll need to be a Slack admin in your workspace to follow these steps.

1. Create a private Slack channel (ours is named `extension-bot`). Add anyone who's approved to manage/view accommodations and DSP information should be added to the channel.
2. [Create a Slack webhook](https://api.slack.com/messaging/webhooks), and point it towards your newly created channel. Feel free to skip past all of the reading and follow these steps –
   - Click the big green "Create your Slack App" button.
   - Select "From scratch" and enter "ExtensionBot" as the name. Select your workspace.
   - Click "Incoming Webhooks" in the sidebar, scroll down, and create a new web hook.
   - Save the URL. We'll need it later.

### Part 2: Configuring Google Forms/Sheets

_Estimated Time: 10 minutes_

**Cloning the Form/Sheet**

1. Make a copy of [this spreadsheet](https://docs.google.com/spreadsheets/d/1BabID1n6fPgeuuO4-1r3mkoQ9Nx5dquNwdsET75In1E/edit?usp=sharing). Make sure to rename it to "CS \_\_\_ SP22 Extensions Backend"
2. Delete the “Form Responses” sheet within the spreadsheet.
3. Share the spreadsheet with [cs-161-extensions@appspot.gserviceaccount.com](mailto:cs-161-extensions@appspot.gserviceaccount.com). This allows our hosted cloud function to read/write to your sheet. (If you're self-hosting, this should be your service account email.)
4. Make a copy of [this form](https://docs.google.com/forms/d/1_9XobNT4R3z_bhlrVEUqMP92Bxa9W5FsedNngZuGwXc/edit?usp=sharing). Make sure to rename it. Close the form template, so you don't accidentally edit it.
5. On the form, in the "Responses" tab, configure the form responses to be written to the Extensions Backend spreadsheet.
   - This should create a new tab within the Extensions Backend sheet.
   - Rename the tab to “Form Responses”.
6. **Set the header of column M of the Form Responses sheet to "Rerun"**. Then, select all of the rows of that column, and insert a checkbox using "Insert" => "Checkbox".

**Configuring Apps Script**

7. On the **Spreadsheet**, open the **Extensions => Apps Script** menu option.

   - Rename the script to "CS \_\_\_\_ SP22 Extension Requests Script".

   - Click on "Triggers" in the sidebar (the little clock icon).

   - Add a **onFormSubmit** trigger that looks like this:
     ![img](GETTING_STARTED.assets/0Ur-tyYJ95715JEYTO3McmVlv8UXtcuSj448PzjfeVY1SWfRJO7X6lSl6_S5bWEsb2pa8WHg75BhFNfvNx65NZG9IbZv_QxrN3l3aZBqY97EDJLBS8tcW1ktBP9fwqZ512G5Tsy3-3315320.png)

**Configuring Roster**

There isn't much you need to do to configure the roster! If you want to add your students here ahead of time, feel free to add a list of names, emails, and SID's. If you don't, students will be added "on-demand" (e.g. when a student submits an extension request). If a student submits several requests, their roster record will be updated in-place.

The `name` and `sid` columns are optional - feel free to delete them if you don't need them. The `notes` column is for your own use.

**Configuring Assignments**

9. On the **Spreadsheet/Assignments** tab:
   - Each assignment should have a unique Assignment ID.
   - Set a due date in YYYY-MM-DD format for each assignment, and a partner status (either "Yes" or "No").
10. On the **Spreadsheet/Roster** tab:

    - Each assignment should have a single column.
    - The column headers should match the assignment ID's in the **Assignments** tab.

11. On the **Form**:
    - Update the assignment options to match the names in the **Assignments** tab.

**Configuring Form Questions**

12. If you'd like to edit any of the form question descriptions, feel free to do so. Make sure to check the **Form Questions** spreadsheet to ensure that the question/key pairings are valid; you may have to paste this formula into cell A2 if you see a red error message. `=TRANSPOSE('Form Responses'!A1:X1)`

**Configuring Environment Variables**

13. Finally, configure Environment Variables as desired - instructions are within the sheet! This is where you should paste your `SLACK_ENDPOINT` .
    - The `SLACK_ENDPOINT_DEBUG` webhook is an optional configuration variable: it pipes all debug logs to a CS 161 internal Slack channel. Feel free to delete this row after your system is up and running!
    - The `EMAIL_FROM` field can be any email, but it should be formatted as "Sender Name <some-email@berkeley.edu>".

### Part 3: Configuring Gradescope (Optional)

*Estimated Time: 5 minutes*

If you'd like your approved extensions to be reflected in Gradescope (using the assignment "extensions" feature), you'll need to configure a staff API account.

14. Add `cs000-staff+api@berkeley.edu` (or another email address - typically an alias of your SPA email address) as an instructor to the current semester's Gradescope course.
15. Sign in with that email (reset your password if you don't recieve an email from Gradescope when you're added).
16. Paste the email/password combination in the `GRADESCOPE_EMAIL` and `GRADESCOPE_PASSWORD` environment variables.
17. Add one or more comma-separated Gradescope assignment URL's to each assignment under the `gradescope` column of the "Assignments" sheet.
