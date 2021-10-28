# User Administration

Access the django admin pages here:
https://opportunitymatch.epcc.ed.ac.uk/admin/

Users are added automatically when they log in via EASE for the first time.
Users can also be created *manually*: the Django username must match the EASE UUN 
in order for the system to link the EASE login to the Django account.

To associate a user with a ROAG id, first find the ROAG id by searching for
the user in the research explorer:
https://www.research.ed.ac.uk/portal/
Make a note of the URL for the user, for example:
https://www.research.ed.ac.uk/portal/en/persons/amrey-krause(b0e3c991-6aac-4f97-9e6e-275d20b5ce91).html
and the UUID, in this case `b0e3c991-6aac-4f97-9e6e-275d20b5ce91`.

Now go to 
https://opportunitymatch.epcc.ed.ac.uk/admin/opportunity_match/settings/ and
press "Add Settings +" at the top right.
Select the user, enter the research explorer URL and the UUID for the user.
(The keyword weight can be ignored, it is not used.)
