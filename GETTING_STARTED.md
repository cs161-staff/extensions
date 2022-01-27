# Getting Started

If you'd like us to walk you through setup, feel free to email shomil@berkeley.edu or join the `#161-software-support` channel on EECS Crossroads. That said, all of this is self-serve, so you could follow this guide entirely by yourself if you'd like!

It takes ~30 minutes to onboard your class onto this tool, and that time pays off as soon as your first extension requests start rolling in :) 

### Part 1: Configuring Slack

*Estimated Time: 5 minutes*

You'll need to be a Slack admin in your workspace to follow these steps.

1. Create a private Slack channel (ours is named `extension-bot`). Add anyone who's approved to manage/view accommodations and DSP information should be added to the channel.
2. [Create a Slack webhook](https://api.slack.com/messaging/webhooks), and point it towards your newly created channel. Feel free to skip past all of the reading and follow these steps –
   - Click the big green "Create your Slack App" button.
   - Select "From scratch" and enter "ExtensionBot" as the name. Select your workspace.
   - Click "Incoming Webhooks" in the sidebar, scroll down, and create a new web hook.
   - Save the URL. We'll need it later.

### Part 2: Configuring SendGrid

*Estimated Time: 10 minutes*

We're currently working on improving this step so that each course doesn't need its own SendGrid account. That said, these steps should be pretty self explanatory!

1. Create a SendGrid account. **Verify your email.**
2. In SendGrid, create a new Single Sender. **Verify the single sender email.**
3. In SendGrid settings, create a new API Key with full access. Save the API key. We'll need it later.

### Part 3: Configuring Google Forms/Sheets

**Cloning the Form/Sheet**

1. Make a copy of [this spreadsheet](https://docs.google.com/spreadsheets/d/1BabID1n6fPgeuuO4-1r3mkoQ9Nx5dquNwdsET75In1E/edit?usp=sharing). Make sure to rename it to "CS ___ SP22 Extensions Backend"
2. Delete the “Form Responses” sheet within the spreadsheet.
3. Share the spreadsheet with [sheets-service@cs-161-extensions.iam.gserviceaccount.com](mailto:sheets-service@cs-161-extensions.iam.gserviceaccount.com). This allows our hosted cloud function to read/write to your sheet. (If you're self-hosting, this should be your service account email.)
4. Make a copy of [this form](https://docs.google.com/forms/d/1_9XobNT4R3z_bhlrVEUqMP92Bxa9W5FsedNngZuGwXc/edit?usp=sharing). Make sure to rename it. Close the form template, so you don't accidentally edit it.
5. On the form, in the "Responses" tab, configure the form responses to be written to the Extensions Backend spreadsheet.
   - This should create a new tab within the Extensions Backend sheet. 
   - Rename the tab to “Form Responses”.
6. **Set the header of column M of the Form Responses sheet to "Rerun"**. Then, select all of the rows of that column, and insert a checkbox using "Insert" => "Checkbox".

**Configuring Apps Script**

7. On the **Spreadsheet**, open the **Extensions => Apps Script** menu option.

   - Rename the script to "CS ____ SP22 Extension Requests Script".

   - Click on "Triggers" in the sidebar (the little clock icon).

   - Add a **onFormSubmit** trigger that looks like this:
     ![img](GETTING_STARTEd.assets/0Ur-tyYJ95715JEYTO3McmVlv8UXtcuSj448PzjfeVY1SWfRJO7X6lSl6_S5bWEsb2pa8WHg75BhFNfvNx65NZG9IbZv_QxrN3l3aZBqY97EDJLBS8tcW1ktBP9fwqZ512G5Tsy3-3315320.png)

**Configuring Roster**

8. For now, add one or a few rows to the roster with your own names/emails/SID's that you can test with. 
    - The only columns you need to edit are "name", "email", and "sid". 
    - The "type" column isn't used for anything (it's there to help you categorize students - e.g. "Waitlisted", "Enrolled", "GLOBE", etc.).

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

13. Finally, configure Environment Variables as desired - instructions are within the sheet! This is where you should paste your `SENDGRID_API_KEY` and `SLACK_ENDPOINT` .
    - The `SLACK_ENDPOINT_DEBUG` webhook is an optional configuration variable: it pipes all debug logs to  a CS 161 internal Slack channel. Feel free to delete this row after your system is up and running!