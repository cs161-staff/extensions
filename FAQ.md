[!WARNING]
This site is under construction and is subject to change while this message is still visible. 

This page will list out quick responses, common bugs and their fixes, as well as workflow suggestions. 

[Jordan's Fa23 tips and tricks](https://docs.google.com/document/d/1_BOKVyhKW8_-tmgtV5qpVAi33aKYKpKd1WmnPCzsYOg/edit?usp=sharing)

# FAQs
## While getting started
* [Do I need to ask if students are enrolled in DSP?](#do-i-need-to-ask-if-students-are-enrolled-in-dsp)
* [I want to modify the email sent to students!](#modify-email)
## After walking through [GETTING_STARTED.md](https://github.com/cs161-staff/extensions/blob/master/GETTING_STARTED.md)
* [The Form Responses tab is filling, but the Roster tab is not](#the-form-responses-tab-is-filling-but-the-roster-tab-is-not)
* [I need to change the name of the slack channel](#i-need-to-change-the-name-of-the-slack-channel)
## Error messages
* ["Student \<name\> responded '' to DSP question in extension request, but is not marked for DSP approval on the roster. Please investigate!"](#snr)
* ["Error: ('An error occurred while sending an email:', Exception(... Insufficient system storage', 'cs162ta@cs162.eecs.berkeley.edu'))"](#cs162)

### Do I need to ask if students are enrolled in DSP?
>So your course's extension policy is not different for students enrolled in DSP, no worries! Unfortunately, at this point in time, the script relies on there being a DSP question asked in the form. That being said, the example form as it currenly is prevents students from seeing the question, since 161 no longer uses DSP data to decide how to grant exensions. So you *must* keep this question in the google form, but students don't have to respond to it. See []() for more details. 

<div id="modify-email"></div>

### I want to modify the email sent to students!
>You can use the built in method of the email column comments! Check out [an example here.](https://docs.google.com/spreadsheets/d/17-NKHpKrdW-1t1SoxMXHBvfF-Dery6lfefhPUW62WQM/edit?usp=sharing)

>Feel free to [fork](https://docs.github.com/en/get-started/quickstart/fork-a-repo) this repo to create your own email template1

### The Form Responses tab is filling, but the Roster tab is not
>One really common cause of this is forgetting to share the google sheet with the google api: cs-161-extensions@appspot.gserviceaccount.com (Part 2, step 3 of Getting Started)

>If you've done that but it still isn't working, another possible fix is to try filling the student email column with the entire remaining roster.

### I need to change the name of the slack channel
>No problem! Changing the name of the slack channel where the webhook points will not affect it. You should be able to do this with no consequences.

<div id="snr"></div>

### "Student \<name\> responded '' to DSP question in extension request, but is not marked for DSP approval on the roster. Please investigate!" 

>1. the dsp question is not visible to students but exists in the form so that the backend doesn't error. the response to this question will default to ‘’. That causes the response “Student <email> responded ‘’ to DSP question in extension request, but is not marked for DSP approval on the roster. Please investigate!”
>    1. You can get rid of this error by deleting the "is_dsp" column from the roster tab. *Don't remove it from Form Questions*
>1. the dsp question is visible to students, but there is no option for "No". the response to this question will default to ''. That causes the response “Student <email> responded ‘’ to DSP question in extension request, but is not marked for DSP approval on the roster. Please investigate!”
>1. the dsp question is visible to students, they select yes, their row does not yet exist in the roster spreadsheet. That causes a response along the lines “Student responded ‘yes’ to DSP question but is not a DSP student”. You can prevent the response, by going into the roster tab in the backend and marking them down as Yes in the DSP? column. You can do this in 2 ways:
>    1. add all dsp students to the roster before the semester starts and mark them as yes in the dsp column
>    1. whenever a student responds themselves as yes to the dsp question, check in AIM, and then update the dsp column to reflect their response
>1. the dsp question is visible to students and their response is “No”. this will not appear in the response from extension bot

<div id="cs162"></div>

### "Error: ('An error occurred while sending an email:', Exception(... Insufficient system storage', 'cs162ta@cs162.eecs.berkeley.edu'))"
>This is an error with the mailing server we use to send emails, hosted by CS 162 at UC Berkeley. Please contact them! You can either ping in #161-extensions in EECS Crossroads or, as of Fa23, contact Wilson Nguyen.