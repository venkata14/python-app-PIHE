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

# Download this from the Internet
df = pd.read_csv('employees.csv')

# Templates
template_email = """Dear {0},

My name is {1} and I am a constituent from {2}. Could I meet with {3} {4} to talk about NOVID?

Thank you,
{1}"""

subject = "Meeting Request"

# Variables
submitted = False
address = False
found_reps = False
global email_box_open
email_box_open = False

# Format the layout
introduction = st.container()
look_up_container = st.container()
reps = st.container()
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
    address = address + ' x'

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
            return senetor1, senetor2, representative1, found_reps
        except requests.exceptions.Timeout:
            # Maybe set up for a retry, or continue in a retry loop
            st.write("Connection Timed Out. Please try again.")
            return [], [], [], False
        except requests.exceptions.TooManyRedirects:
            # Tell the user their URL was bad and try a different one
            st.write("Too many redirects. Bad input")
            return [], [], [], False
        except Exception as e:
            st.write('An Error occured when trying to identify your representatives. **Please use a more accurate Address.**')
            return [], [], [], False
    else:
        return [], [], [], False

senetor1, senetor2, representative1, found_reps = get_mocs()

# If the reps have been found 
if found_reps:
    with reps:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.header("First Senator")
            st.info(''.join(["##### ", senetor1, '\n', 'Scheduler: ', ]))
            
        with col2:
            st.header("Second Senator")
            st.info(''.join(["##### ", senetor2, '\n', 'Scheduler: ', ]))
        
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
                    email_info = [selected_index, 'representative']
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
                    email_info = [selected_index, 'representative']
                    submitted = st.form_submit_button("Email")
                st.dataframe(
                         show_info
                    )


if email_box_open:
    with name_container:
        viewer_name = st.text_input("Full Name", placeholder="Name")
        # Make this an auto validator for the email
        viewer_email = st.text_input("Your Email", placeholder="Email")


if email_box_open:
    with email_box:
        with st.form('email-box'):
            subject = st.text_input('Subject', value=subject)
            if email_info[1] == 'representative':
                temp_email_intermediate = email_info[0].split(',')
                temp_email_intermediate = ''.join(temp_email_intermediate)
                temp_email_intermediate = temp_email_intermediate.split()
                last_name_int, first_name_int = temp_email_intermediate[0].lower(), temp_email_intermediate[1].lower()
                # Run an API validator on this email
                scheduler_email_value = ''.join([first_name_int, '.', last_name_int, '@mail.house.gov'])
                scheduler_email = st.text_input("Scheduler Email", value=scheduler_email_value, placeholder="Email")
                message = st.text_area('Message', value=template_email.format(
                                                        ' '.join([first_name_int.capitalize(), last_name_int.capitalize()]), 
                                                        viewer_name, 
                                                        address, 
                                                        "Representative", 
                                                        representative1),
                                       height=500,
                                       )
                
            elif email_info[1] == 'senator':
                pass
            
            
            email_submitted = st.form_submit_button("Generate Email Link")
            if email_submitted:
                params = {
                    'to': scheduler_email, 
                    'su': subject,
                    'body': message
                    }
                URL_meta_data = urllib.parse.urlencode(params)
                email_link_url = ''.join(['https://mail.google.com/mail?view=cm&tf=0&', URL_meta_data])
                st.markdown("""[Email Link]({0})""".format(email_link_url), unsafe_allow_html=True)

    
