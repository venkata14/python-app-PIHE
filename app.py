import streamlit as st
import pandas as pd
import numpy as np
import requests
import urllib.parse
# import streamlit.components.v1 as components
# from streamlit import legacy_caching

# Page styling
st.set_page_config(page_title="Legislative Lookup/Email",
                   layout="wide"
                   )

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            footer:after {
                content:'Made by Venkata Patchigolla w/ Streamlit'; 
                visibility: visible;
                display: block;
                position: absolute;
                right: 0;
                #background-color: red;
                padding: 5px;
                top: 2px;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

API_KEY = st.secrets["API_KEY"]

# Download this from the Internet for the representatives
df = pd.read_csv('employees.csv')

# For the senetors
gsheetid = "1dDOJi4lSnZqEo27hKOVGY2047952aili5LgNe5jrF7E"
sheet_name = "Emails"
template_sheet_name = "Templates"
gsheet_url = "https://docs.google.com/spreadsheets/d/{}/gviz/tq?tqx=out:csv&sheet={}".format(gsheetid, sheet_name)
template_email_url = "https://docs.google.com/spreadsheets/d/{}/gviz/tq?tqx=out:csv&sheet={}".format(gsheetid, template_sheet_name)
df_sen = pd.read_csv(gsheet_url)

# For the template email and subject
try:
    df_template = pd.read_csv(template_email_url)

    # Templates
    template_email = df_template['Email Template'].tolist()[0]

    subject = df_template['Subject'].tolist()[0]
except:
    st.write("There was an eroor retrieving the PIHE templates")
    template_email = """Dear {0},
 
My name is {1}, and I am a constituent from {2} interested in access to health care in the U.S. and globally. I also volunteer with Partners In Health Engage, which is a grassroots network of citizens advocating for health care.
   
I'd like to schedule a meeting shortly to discuss legislation for strengthening global health systems. I [along with other constituents] am hoping to meet briefly with {3} {4} or a member of their [foreign policy staff/health policy staff] to discuss these important issues. [insert any personal note here (e.g. “I am aware that Rep Chabot is a member of the House Foriegn Affairs committee, and I believe that advancing global health equity is an aligned interest of Partners In Health Engage and HFAC.”)]
 
Would a meeting in the coming days be possible? If so, what times would work well? Thank you very much for considering this request, and I look forward to hearing from you.
 
Sincerely,
 
{1}
"""
    subject = "Meeting Request"

# Variables
submitted = False
address = False
found_reps = False
global email_box_open
email_box_open = False
normalized_address = None

# Format the layout
introduction = st.container()
look_up_container = st.container()
reps = st.container()
choose_who_to_email = st.container()
name_container = st.container()
email_box = st.container()


with introduction:
    # Notes on How this works
    st.markdown("""
# Demo

How does this app work?

*Note* Only the House of Reps works at this time.

1. Type in your address. Does not need to be an exact address. If it throws an error, it requires a more accurate address.
2. Choose who to email and click the "Email"
3. Type your name and email.
4. Edit your template.
5. Click on "Generate Email Link".
6. Click on the link generated. It currently only works for Gmail. It opens a new tab and autofills the emails section.
""")
    st.title("PIHE App - Scheduling Meetings with MOCs")
    
# Get address
with look_up_container:
    st.write("Legislative LookUp")
    address = st.text_input("Address (Doesn't need to be specific. Ex: 'Storrs, CT' if your are from a small town.", placeholder="Address")
    address = address

    # Every form must have a submit button.
    # submitted = st.button("Submit")
    submitted = True

# Getting Senetor Names
@st.cache(suppress_st_warning=True)
def get_mocs():
    if address:
        params = {
            'address': address,
            'level': 'country',
            'key': API_KEY
        }
        
        # dealing with bad inputs or bad api
        try:
            response = requests.get("https://www.googleapis.com/civicinfo/v2/representatives", params=params)
            response_json = response.json()
            senetors = []
            representative = []
            for n in response_json['offices']:
                if n["name"] == "U.S. Senator":
                    senetors.extend(n["officialIndices"])
                elif n["name"] == "U.S. Representative":
                    representative.extend(n["officialIndices"])
            
            # The Normalized Addess for the template
            NAR = response_json['normalizedInput']
            normalized_address = ' '.join([NAR['line1'], NAR['city'] + ',' , NAR['state'], NAR['zip']])
            
            senetors_info = []
            representative_info = []
            
            for n in senetors:
                senetors_info.append(response_json['officials'][n])
            
            for n in representative:
                representative_info.append(response_json['officials'][n])
            
            # Make this more robust
            senetor1 = senetors_info[0]['name']
            senetor2 = senetors_info[1]['name']
            representative1 = representative_info[0]['name']
            
            found_reps = True
            st.write(response_json)
            
            return senetor1, senetor2, representative1, found_reps, normalized_address
        except requests.exceptions.Timeout:
            # Maybe set up for a retry, or continue in a retry loop
            st.write("Connection Timed Out. Please try again.")
            return [], [], [], False, None
        except requests.exceptions.TooManyRedirects:
            # Tell the user their URL was bad and try a different one
            st.write("Too many redirects. Bad input")
            return [], [], [], False, None
        except Exception as e:
            st.write('An Error occured when trying to identify your representatives. **Please use a more accurate Address.**')
            return [], [], [], False, None
    else:
        return [], [], [], False, None


senetor1, senetor2, representative1, found_reps, normalized_address = get_mocs()

# If the reps have been found 
if found_reps:
    with reps:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.header("First Senator")
            last_name = senetor1.split()[-1].capitalize()
            # Filtering the results to the senetor of interest
            office_data = df_sen[df_sen['Congressional member'].str.lower().str.contains(last_name.lower())]
            # Scheduler
            scheduler = office_data['Scheduler'].tolist()[0]
            s_first_name = scheduler.split()[0]
            s_last_name = scheduler.split()[1]
            scheduler_email = office_data['Email'].tolist()[0]
            st.info(''.join(["##### ", senetor1, '\n', 'Scheduler: ', scheduler]))
            st.dataframe(office_data)
            email_box_open= True
            email_info_senetor1 = [scheduler_email, 'senator1', last_name, s_first_name, s_last_name]
            
        with col2:
            st.header("Second Senator")
            last_name = senetor2.split()[-1].capitalize()
            # Filtering the results to the senetor of interest
            office_data = df_sen[df_sen['Congressional member'].str.lower().str.contains(last_name.lower())]
            # Scheduler
            scheduler = office_data['Scheduler'].tolist()[0]
            s_first_name = scheduler.split()[0]
            s_last_name = scheduler.split()[1]
            scheduler_email = office_data['Email'].tolist()[0]
            st.info(''.join(["##### ", senetor2, '\n', 'Scheduler: ', scheduler]))
            st.dataframe(office_data)
            email_box_open= True
            email_info_senetor2 = [scheduler_email, 'senator2', last_name, s_first_name, s_last_name]
        
        with col3:
            last_name = representative1.split()[-1].capitalize()
            office_data = df[df["Office"].str.contains(last_name)]
            st.header("Representative")
            st.info(''.join(["##### ", representative1, '\n', 'Scheduler: ', ]))
            titles = office_data['Title'].copy()
            scheduler = titles.str.lower().str.contains("scheduler")
            
            number_results = scheduler.sum()
            if number_results == 0:
                show_info = office_data[['Name', 'Title', 'Phone']]
                show_info.set_index('Name', inplace=True)
                
                # new_title = st.selectbox('This MOC does not have a scheduler. Use another Title from the "Title" column below', show_info.index)
                # if new_title:
                #     st.text(new_title)
                #     email_box_open= True
                #     email_info = [new_title, 'representative']
                with st.form('scheduler-representative'):
                    selected_index = st.selectbox('This MOC does not have a scheduler. You can instead email another staffer. We recommend you email a *Director* or a *Staff Assistant*', show_info.index)
                    st.text(selected_index)
                    email_box_open= True
                    email_info_representative = [selected_index, 'representative', last_name]
                    submitted = st.form_submit_button("Email")
                key_words = ['director','staff assistant']  
                regstr = '|'.join(key_words)
                bool_map_recs = show_info['Title'].copy()
                recommendations = show_info[bool_map_recs.str.lower().str.contains(regstr)]
                
                show_rec = st.checkbox('Show Recommended Personal', value=True)
                show_all = st.checkbox('Show All Personal')
                    
                # st.write('###### *Recommended Personal*')
                if show_rec:
                    st.dataframe(recommendations)
                # st.write('###### *All Personal*')
                if show_all:
                    st.dataframe(show_info)
                
            else:
                show_info = office_data[scheduler][['Name', 'Title', 'Phone']]
                show_info.set_index('Name', inplace=True)
                with st.form('scheduler-representative'):
                    selected_index = st.selectbox('Select who to email', show_info.index)
                    st.text(selected_index)
                    email_box_open= True
                    email_info_representative = [selected_index, 'representative', last_name]
                    submitted = st.form_submit_button("Email")
                st.dataframe(
                         show_info
                    )
                

# Choose who to email
if email_box_open:
    with choose_who_to_email:
        st.write("## ")
        st.write("#### ")
        st.write("## Pick a representative to email (Choose one)")
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        who_to_email_map = [False, False, False]
        with col1:
            if st.checkbox('Senetor ' + email_info_senetor1[2], value=True):
                who_to_email_map[0] = True
        with col2:
            if st.checkbox('Senetor ' + email_info_senetor2[2]):
                who_to_email_map[1] = True
        with col3:
            if st.checkbox('Representative ' + email_info_representative[2]):
                who_to_email_map[2] = True
        
        # Make sure there is not more than 1 person to email
        if np.sum(who_to_email_map) == 1:
            if who_to_email_map[0] == True:
                email_info = email_info_senetor1
            elif who_to_email_map[1] == True:
                email_info = email_info_senetor2
            elif who_to_email_map[2] == True:
                email_info = email_info_representative
        else:
            st.error("You can only pick one representative at a time to email.")
            if who_to_email_map[0] == True:
                email_info = email_info_senetor1
            elif who_to_email_map[1] == True:
                email_info = email_info_senetor2
            elif who_to_email_map[2] == True:
                email_info = email_info_representative

# Your personal Informaion
if email_box_open:
    with name_container:
        st.write("## ")
        st.write("#### ")
        st.write("## Enter Your Information")
        st.markdown("---")
        col1, col2 = st.columns(2)
            
        # This is the user information
        with col1:
            viewer_name = st.text_input("Full Name", placeholder="Name")
            # Make this an auto validator for the email
            viewer_email = st.text_input("Your Email", placeholder="Email")
        
        with col2:
            cc_email = st.text_input("Cc", placeholder="Cc", value="engagescheduler@gmail.com")
            bcc_email = st.text_input("Bcc", placeholder="Bcc")

# The message box
if email_box_open:
    with email_box:
        with st.form('email-box'):
            # This is the email logic
            subject = st.text_input('Subject', value=subject)
            if email_info[1] == 'representative':
                temp_email_intermediate = email_info[0].split(',')
                temp_email_intermediate = ''.join(temp_email_intermediate)
                temp_email_intermediate = temp_email_intermediate.split()
                last_name_int, first_name_int = temp_email_intermediate[0].lower(), temp_email_intermediate[1].lower()
                which_house = "Representative"
                rep_name = representative1.split()[-1].capitalize()
                # Run an API validator on this email
                scheduler_email_value = ''.join([first_name_int, '.', last_name_int, '@mail.house.gov'])
            elif email_info[1] == 'senator1':
                scheduler_email_value = email_info[0]
                first_name_int = email_info[3]
                last_name_int = email_info[4]
                which_house = "Senetor"
                rep_name = senetor1.split()[-1].capitalize()
            elif email_info[1] == 'senator2':
                scheduler_email_value = email_info[0]
                first_name_int = email_info[3]
                last_name_int = email_info[4]
                which_house = "Senetor"
                rep_name = senetor2.split()[-1].capitalize()
            else:
                st.write("Error. That's all we know :/")
                scheduler_email_value = email_info[0]
            
            # This is the scheduler email box
            scheduler_email = st.text_input("Scheduler Email", value=scheduler_email_value, placeholder="Email")
            message = st.text_area('Message', value=template_email.format(
                                                    ' '.join([first_name_int.capitalize(), last_name_int.capitalize()]), 
                                                    viewer_name, 
                                                    normalized_address, 
                                                    which_house, 
                                                    rep_name),
                                    height=500,
                                    )
            email_submitted = st.form_submit_button("Generate Email Link")
            
            if email_submitted:
                if "" in [viewer_name, viewer_email, cc_email, scheduler_email, subject, message]:
                    st.error("You must fill in all values except for Bcc. There are several empty responces.")
                else:
                    params = {
                        'to': scheduler_email, 
                        'su': subject,
                        'body': message
                        }
                    URL_meta_data = urllib.parse.urlencode(params)
                    email_link_url = ''.join(['https://mail.google.com/mail?view=cm&tf=0&', URL_meta_data])
                    st.markdown("""[Email Link]({0})""".format(email_link_url), unsafe_allow_html=True)

    
