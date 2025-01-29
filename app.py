import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from datetime import date as dt
import os
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
import base64
import hashlib

st.set_page_config(layout="wide")

st.markdown("""
    <style>
        header {visibility: hidden;}      
    </style>
    """, unsafe_allow_html=True)

def check_password():
    def make_hash(password):
        return hashlib.sha256(str.encode(password)).hexdigest()
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True

    dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
    bg_path = dir / "images" / "SJA.png"
    
    def get_base64_encoded_image(bg_path):
        with open(bg_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
        
    st.markdown(f"""
    <style>
                
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/jpg;base64,{get_base64_encoded_image(str(bg_path))}");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
            align-items: center;
            justify-content: center;
        }}
    </style>    
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:

        st.markdown('')
        with st.form(key='login_form'):
            st.markdown(
                """
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Ubuntu&display=swap');
                    
                    .stForm {
                        
                        color: rgb(0, 0, 0);
                        width: 700px;
                        height: 400px;
                        box-shadow: 0 0 10px rgba(10, 10, 10, 0.5);
                        margin-left: auto;
                        margin-right: auto;
                        display: block;
                        border-radius: 20px;

                    }
                    .login-title {
                        font-family: 'Ubuntu', sans-serif;
                        font-size: 28px;
                        color: black;
                        text-align: center;
                    }
                    .stFormSubmitButton>button {
                        background-color: #162938;
                        width: 100%;
                        height: 45px;
                        color: white;
                    }

                    .stFormSubmitButton>button:hover {
                        background-color: #FF3333;
                        border: none;
                        color: white;
                    }
                    .stTextInput input {
                        background-color: #16293825;
                        border-radius: 10px;
                        padding: 10px;
                    }
                        
                </style>
                <h1 class="login-title">Admin Login</h1>
                """, 
                unsafe_allow_html=True
            )
            username = st.text_input('Username', placeholder='Enter Username')
            password = st.text_input('Password', type='password', placeholder='Enter Password')

            login_button = st.form_submit_button(label='Sign in')
            
            if login_button:
                if username == "admin" and password == "sjalibrary":
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            st.markdown('')
           
    st.markdown(
        "<p style='text-align: center; color: rgba(255,255,255,0.5); position: fixed; bottom: 20px; width: 100%; left: 0;'>"
        "© 2024 Library Management System. All rights reserved.</p>",
        unsafe_allow_html=True
    )
    return False


if check_password():

    def set_background():
        current_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
        image_path = current_dir / "images" / "SJA.png"
        
        page_bg_img = f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/png;base64,{get_base64_encoded_image(str(image_path))}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-blend-mode: darken;
        }}

        </style>
        """
        st.markdown(page_bg_img, unsafe_allow_html=True)

    def get_base64_encoded_image(image_path):
        import base64
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return encoded_string

    set_background()
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


    def update_book_status(df):
        def count_borrowers(patron_str):
            if pd.isna(patron_str) or patron_str == '':
                return 0
            return len([p for p in str(patron_str).split(',') if p.strip()])
        
        df['Borrowers_Count'] = df['Patron'].apply(count_borrowers)
        df['Status'] = df.apply(lambda row: 'Inactive' if row['Borrowers_Count'] >= row['Quantity'] else 'Active', axis=1)
        df.drop('Borrowers_Count', axis=1, inplace=True)
        return df
    

    def save_inventory_to_xlsx(data, file_path='Database.xlsx'):
        if os.path.exists(file_path):
            existing_data = pd.read_excel(file_path, dtype={'ISBN': str})
            existing_data['ISBN'] = existing_data['ISBN'].str.strip()
            
            matching_book = existing_data[existing_data['ISBN'] == data['ISBN'].strip()]
            
            if not matching_book.empty:
                book_idx = matching_book.index[0]
                existing_data.at[book_idx, 'Quantity'] += data['Quantity']
                updated_data = existing_data
            else:
                updated_data = pd.concat([existing_data, pd.DataFrame([data])], ignore_index=True)
        else:
            updated_data = pd.DataFrame([data])
        
        updated_data = update_book_status(updated_data)
        updated_data.to_excel(file_path, index=False)
        return updated_data


    def count_borrowed_books(patron_string):
        if pd.isna(patron_string) or patron_string == '':
            return 0
        return len([date for date in str(patron_string).split(',') if date.strip()])

    def create_scanner_input(key, placeholder="Scan or enter ISBN"):
        isbn = st.text_input("ISBN", key=key, placeholder=placeholder, help="Use barcode scanner or enter manually")
        return isbn
    
    def log_transaction(transaction_type, isbn, student_name, year_level, section):    
        transaction_file = 'Transaction.xlsx'
        if os.path.exists(transaction_file):
            transactions_df = pd.read_excel(transaction_file)
        else:
            transactions_df = pd.DataFrame(columns=[
                'Transaction ID', 
                'Transaction Type', 
                'ISBN', 
                'Book Title',
                'Author',
                'Patron Name', 
                'Year Level', 
                'Section', 
                'Transaction Date',
                'Status'
            ])

        isbn = str(isbn).strip()
        
        try:
            inventory_df = pd.read_excel('Database.xlsx', dtype={'ISBN': str})
            

            inventory_df['ISBN'] = inventory_df['ISBN'].str.strip()
            
            matching_books = inventory_df[inventory_df['ISBN'] == isbn]
            
            if matching_books.empty:
                print(f"No book found with ISBN: {isbn}")
                book_title = "Not Found"
                book_author = "Not Found"
            else:
                book_details = matching_books.iloc[0]
                book_title = book_details['Book Title']
                book_author = book_details['Author']
                print(f"Found book: {book_title} by {book_author}")  
                
        except Exception as e:
            print(f"Error accessing inventory: {str(e)}")
            book_title = "Error"
            book_author = "Error"

        new_transaction = {
            'Transaction ID': len(transactions_df) + 1,
            'Transaction Type': transaction_type,
            'Transaction Date': dt.today().strftime('%Y-%m-%d %H:%M:%S'),
            'ISBN': isbn,
            'Book Title': book_title,
            'Author': book_author,
            'Patron Name': student_name,
            'Year Level': year_level,
            'Section': section,
            'Status': 'Successful'
        }
        
        transactions_df = pd.concat([transactions_df, pd.DataFrame([new_transaction])], ignore_index=True)
        transactions_df.to_excel(transaction_file, index=False)

    def get_transaction_history(isbn=None, student_name=None):

        if not os.path.exists('Transaction.xlsx'):
            return pd.DataFrame()     
        transactions_df = pd.read_excel('Transaction.xlsx')

        if isbn:
            transactions_df = transactions_df[transactions_df['ISBN'] == isbn]
        if student_name:
            transactions_df = transactions_df[transactions_df['Patron Name'] == student_name]
            
        return transactions_df
    
    def load_inventory():
        if os.path.exists('Database.xlsx'):
            return pd.read_excel('Database.xlsx', dtype={'ISBN': str})
        return None

    def save_inventory(df):
        df.to_excel('Database.xlsx', index=False)

    def edit_inventory_item(df, isbn, updates):
        try:
            if isbn in df['ISBN'].values:
                for column, value in updates.items():
                    if column in df.columns:
                        df.loc[df['ISBN'] == isbn, column] = value
                df = update_book_status(df)
                save_inventory(df)
                return df
            return None
        except Exception as e:
            print(f"Error updating inventory: {e}")
            return None

    def delete_inventory_item(df, isbn):

        if isbn in df['ISBN'].values:
            book_row = df[df['ISBN'] == isbn].iloc[0]
            if pd.notna(book_row['Patron']) and book_row['Patron'] != '':
                return None, "Cannot delete book that is currently borrowed"
            
            df = df[df['ISBN'] != isbn]
            save_inventory(df)
            return df, "Book deleted successfully"
        return None, "Book not found"




    def dashboard():
        st.sidebar.image("images/logo.png")           
        with st.sidebar:
            selected = option_menu(
                menu_title = 'Dashboard',
                options = ['Home', 'Inventory', 'Check Out','Check In', 'Record', 'Log Form', 'Sign Out'],
                menu_icon = 'speedometer2',
                icons = ['house-fill','collection', 'bookmark-check-fill', 'back', 'folder-fill', 'clipboard-data', 'box-arrow-left'],
            )
        

        #-------------------------------------------------------- HOME ---------------------------------------------------------------------------

        if selected == 'Home':
            st.markdown(
                """
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Ubuntu&display=swap');
                                        
                    .home-container {
                        width: 100%;
                        background: transparent;
                        display: flex;
                        flex-direction: column;
                        justify-content: flex-end; 
                        align-items: center;
                        min-height: 70vh; 
                        margin: 0; 
                    }

                    .home-container h1 {
                        position: fixed; 
                        text-align: center;
                        width: 100%;
                        left: 160px;
                        bottom: 10px;
                        font-size: 170px;
                        color: #FFFFFF;
                    }
                    .home-container h2 {
                        position: fixed;
                        text-align: center;
                        width: 100%;
                        left: 160px;
                        bottom: 10px;
                        font-size: 40px; 
                        color: #162938;
                        margin-bottom: 0px; 
                    }

                    .home-container h3 {
                        position: fixed;
                        text-align: center;
                        width: 100%;
                        left: 160px;
                        bottom: 10px;
                        font-size: 24px; 
                        margin-bottom: 20px; 
                    }

                </style>

                <div class="home-container">
                    <h2>WELCOME TO</h2>
                    <h1>BiblioGo</h1>
                    <h3>Library Management System</h3>
                </div>
                """, 
                unsafe_allow_html=True
            )
        

        #-------------------------------------------------------- INVENTORY ----------------------------------------------------------------------
        if selected == 'Inventory':
            with st.form(key='inventory_form'):
                st.markdown(
                    """
                    <style>
                    @import url('https://fonts.googleapis.com/css2?family=Ubuntu&display=swap');
                        
                        .inventory-form-title {
                            font-family: 'Ubuntu', sans-serif;
                            font-size: 28px;
                            color: #2a2a2a;
                            text-align: center;
                        }
                    </style>
                    <h1 class="inventory-form-title">SJA Library Management System</h1>
                    <p style="text-align: center;">Fill out the form to add a new item to the inventory.</p>
                    """, 
                    unsafe_allow_html=True
                )


                isbn = create_scanner_input('inventory_isbn')
                book_title = st.text_input('Book Title', value='', key='book_title', placeholder='Enter Book Title')
                author = st.text_input('Author', value='', key='author', placeholder='Enter Author Name')
                    
                col1, col2 = st.columns(2)    
                with col1:
                    
                    type = st.selectbox('Type', options=['Literature', 'Textbooks', 'Journal', 'Research Paper', 'Magazine', ' Brochure'], index=None)
                    publishing_date = st.date_input('Publishing Date', value=dt.today())
                    publishing_date = publishing_date.strftime('%Y-%m-%d')
                    date = st.date_input('Date', value=dt.today())
                    date = date.strftime('%Y-%m-%d')  

                with col2:
                    category = st.selectbox('Category', options=['Fiction','Mathematics', 'Science', 'Filipino','Technology and Livelihood Education (TLE)','Social Studies', 
                                                                 'History',  'Business and Accounting','Literature and Language Arts', 'Technology and Computer Science',
                                                                'Health and Physical Education', 'Art and Music', 'Psychology and Philosophy', 'General Studies'], index=None)
                    acad_level = st.selectbox('Academic Level', options=['Junior High', 'Senior High'], index=None)
                    sub_col1, sub_col2 = st.columns(2)
                    with sub_col1:
                        quantity = st.number_input('Quantity', min_value=1, step=1)
                    with sub_col2:
                        no_pages = st.number_input('Number of Pages', min_value=1, step=1)

                    st.markdown('')
                    submit_button = st.form_submit_button(label='**Add Item**', icon='🗂️')
                    st.markdown('')

                if submit_button:
                    if not book_title or not author or not isbn:
                        st.warning('Please fill out all fields.')
                    else:
                        inventory_data = {
                            'Date': date,
                            'Book Title': book_title,
                            'Author': author,
                            'ISBN': isbn,
                            'Publishing Date': publishing_date,
                            'Type': type,
                            'Category': category,
                            'Quantity': quantity,
                            'No Pages': no_pages,
                            'Academic Level': acad_level,
                            'Patron': '',
                            'Check Out Dates': ''
                        }

                        updated_df = save_inventory_to_xlsx(inventory_data)
                        
                        # Check if it was an update or new addition
                        if len(updated_df[updated_df['ISBN'] == isbn.strip()]) > 0:
                            book_data = updated_df[updated_df['ISBN'] == isbn.strip()].iloc[0]
                            st.success(f'Updated quantity for existing book. New total: {book_data["Quantity"]}')
                        else:
                            st.success('New item has been added successfully!')
                        
            st.markdown("---")

            tab = st.tabs(['Edit Inventory', 'View Inventory', 'Download Inventory'])
            with tab[2]:
                st.subheader('Download Inventory')
             
                with st.expander('Download and Edit Items'):
                    df = load_inventory() 
                    st.data_editor(df, width=None, height=None, use_container_width=False, hide_index=None, column_order=None, column_config=None, num_rows="fixed", disabled=False, key=None, on_change=None, args=None, kwargs=None)
   
            with tab[0]:
                st.subheader('Edit Inventory')
                df = load_inventory()             
                if df is not None:
                    search_term = st.text_input('Search for book to edit (Title/ISBN/Author)', 
                                            key='edit_search',
                                            placeholder='Enter book title, ISBN, or author name')
                    
                    if search_term:
                        mask = (df['Book Title'].str.contains(search_term, case=False, na=False)) | \
                            (df['ISBN'].str.contains(search_term, case=False, na=False)) | \
                            (df['Author'].str.contains(search_term, case=False, na=False))
                        search_results = df[mask]
                        
                        if not search_results.empty:
                            st.dataframe(search_results[['Book Title', 'Author', 'ISBN', 'Quantity', 'Type', 'Category', 'No Pages', 'Publishing Date']], 
                                    use_container_width=True)
                            
                            isbn_list = search_results['ISBN'].tolist()
                            selected_isbn = st.selectbox('Select book to edit:', 
                                                    isbn_list,
                                                    format_func=lambda x: f"{search_results[search_results['ISBN']==x]['Book Title'].iloc[0]} ({x})")
                            
                            if selected_isbn:
                                selected_book = df[df['ISBN'] == selected_isbn].iloc[0]
                                
                                edit_tab, delete_tab = st.tabs(['Edit Book', 'Delete Book'])
                                
                                with edit_tab:
                                    with st.form(key='edit_form'):
                                        st.markdown(
                                            """
                                            <style>
                                                @import url('https://fonts.googleapis.com/css2?family=Ubuntu&display=swap');
                    
                                                .edit-form-title {
                                                    font-family: 'Ubuntu', sans-serif;
                                                    font-size: 28px;
                                                    color: #2a2a2a;
                                                    text-align: center;
                                                }
                                            </style>
                                            <h1 class="edit-form-title">Edit Details</h1>
                                            <p style="text-align: center;">Fill out the form to edit an item to the inventory.</p>
                                            """, 
                                            unsafe_allow_html=True
                                        )
                                        new_title = st.text_input('Book Title', value=selected_book['Book Title'])
                                        new_author = st.text_input('Author', value=selected_book['Author'])
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            new_type = st.selectbox('Type', 
                                                                options=['Literature', 'Textbooks', 'Journal', 'Research Paper', 'Magazine', ' Brochure'],
                                                                index=['Literature', 'Textbooks', 'Journal', 'Research Paper', 'Magazine', ' Brochure'].index(selected_book['Type']))
                                            sub_col1, sub_col2 = st.columns(2)
                                            with sub_col1:
                                                new_quantity = st.number_input('Quantity', 
                                                                            min_value=1, 
                                                                            value=int(selected_book['Quantity'])) 
                                            with sub_col2:
                                                new_no_pages = st.number_input(
                                                    'Number of Pages',
                                                    min_value=1,
                                                    value=int(selected_book['No Pages'] if pd.notna(selected_book['No Pages']) else 1)
                                                )                                        
                                        with col2:
                                            new_category = st.selectbox('Category', 
                                                                    options=['Fiction', 'Mathematics', 'Science', 'Filipino','Technology and Livelihood Education (TLE)','Social Studies', 'History',  'Business and Accounting', 
                                                                            'Literature and Language Arts', 'Technology and Computer Science',
                                                                            'Health and Physical Education', 'Art and Music', 
                                                                            'Psychology and Philosophy', 'General Studies'],
                                                                    index=['Fiction', 'Mathematics', 'Science', 'Filipino','Technology and Livelihood Education (TLE)','Social Studies', 'History',  'Business and Accounting', 
                                                                            'Literature and Language Arts', 'Technology and Computer Science',
                                                                            'Health and Physical Education', 'Art and Music', 
                                                                            'Psychology and Philosophy', 'General Studies'].index(selected_book['Category']))
                                            new_publishing_date = st.date_input('Publishing Date', 
                                                                            value=pd.to_datetime(selected_book['Publishing Date']).date() if pd.notna(selected_book['Publishing Date']) else dt.today())
                                            
                                            update_button = st.form_submit_button('Update Book')
                                        
                                        if update_button:
                                            updates = {
                                                'Book Title': new_title,
                                                'Author': new_author,
                                                'Quantity': new_quantity,
                                                'Type': new_type,
                                                'Category': new_category,
                                                'No Pages': new_no_pages,
                                                'Publishing Date': new_publishing_date.strftime('%Y-%m-%d')
                                            }
                                            
                                            updated_df = edit_inventory_item(df, selected_isbn, updates)
                                            if updated_df is not None:
                                                st.success('Book updated successfully!')
                                                st.rerun()  
                                            else:
                                                st.error('Failed to update book.')

                                
                                with delete_tab:
                                    st.markdown('### Delete Book')
                                    st.write(f"Book Title: {selected_book['Book Title']}")
                                    st.write(f"Author: {selected_book['Author']}")
                                    st.write(f"ISBN: {selected_isbn}")
                                    
                                    confirm_delete = st.checkbox('I confirm that I want to delete this book from the inventory')
                                    
                                    if st.button('Delete Book', disabled=not confirm_delete):
                                        updated_df, message = delete_inventory_item(df, selected_isbn)
                                        if updated_df is not None:
                                            st.success(message)
                                            st.rerun()
                                        else:
                                            st.error(message)
                        else:
                            st.warning('No books found matching your search term.')
                else:
                    st.error('No inventory database found.')

                with tab[1]:
                    st.subheader('Inventory Record')
                    record_data = pd.read_excel('Database.xlsx')
                    sub_tab = st.tabs(['Active Books', 'Inactive Books', 'All Books'])
                    with sub_tab[2]:
                        st.subheader('All Books')
                        def highlight_status(s):
                            return [
                                'background-color: yellow' if s.Status == "Inactive" else ''
                                for _ in s
                            ]

                        with st.expander('All Books'):
                            df = load_inventory()
                            st.dataframe(df.style.apply(highlight_status, axis=1), use_container_width=True)
                    
                    with sub_tab[0]:
                        st.subheader('Active Books')

                        active_books = df[df['Status'] == 'Active']
                        
                        ft_col_list_active = ['Quantity', 'Book Title', 'Author', 'ISBN', 'Type', 'Category', 'Publishing Date', 'No Pages', 'Status']
                        column_widths_active = [1, 4, 4, 4, 2, 2, 2, 1, 2]  

                        active_books_table = go.Figure(
                            data=[go.Table(
                                columnwidth=column_widths_active,
                                hoverlabel=dict(align='auto'),
                                header=dict(
                                    values=[f"<b>{col}</b>" for col in ft_col_list_active],  
                                    font_color='white',
                                    font_size=12,
                                    align='left',
                                    height=18,
                                    fill_color='#ff7b00' 
                                ),
                                cells=dict(
                                    values=[active_books[col] for col in ft_col_list_active], 
                                    font_size=12,
                                    height=24,
                                    align='left',
                                    font_color='black'
                                )
                            )]
                        )

                        active_books_table.update_layout(
                            margin=dict(t=0, b=0, l=0, r=0),
                            height=len(active_books[ft_col_list_active[0]]) * 25 + 50,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)'
                        )

                        st.plotly_chart(active_books_table, use_container_width=True)
                with sub_tab[1]:
                        st.subheader('Inactive Books')

                        active_books = df[df['Status'] == 'Inactive']
                        
                        ft_col_list_active = ['Quantity', 'Book Title', 'Author', 'ISBN', 'Type', 'Category', 'Publishing Date', 'No Pages', 'Status']
                        column_widths_active = [1, 4, 4, 4, 2, 2, 2, 1, 2]  

                        active_books_table = go.Figure(
                            data=[go.Table(
                                columnwidth=column_widths_active,
                                hoverlabel=dict(align='auto'),
                                header=dict(
                                    values=[f"<b>{col}</b>" for col in ft_col_list_active],  
                                    font_color='white',
                                    font_size=12,
                                    align='left',
                                    height=18,
                                    fill_color='#162938' 
                                ),
                                cells=dict(
                                    values=[active_books[col] for col in ft_col_list_active],  
                                    font_size=12,
                                    height=24,
                                    align='left',
                                    font_color='black'
                                )
                            )]
                        )

                        active_books_table.update_layout(
                            margin=dict(t=0, b=0, l=0, r=0),
                            height=len(active_books[ft_col_list_active[0]]) * 25 + 50,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)'
                        )

                        st.plotly_chart(active_books_table, use_container_width=True)
                    
        #-------------------------------------------------------- CHECK OUT ----------------------------------------------------------------------
        if selected == 'Check Out':

            st.subheader('Search for Book to Check Out')
            search_term = st.text_input('Search by Book Title or Author', value='', key='search_term', placeholder='Enter search term')
            if search_term:
                if os.path.exists('Database.xlsx'):
                    df = pd.read_excel('Database.xlsx')
                    search_results = df[df.apply(lambda row: search_term.lower() in row['Book Title'].lower() or search_term.lower() in row['Author'].lower(), axis=1)]
                    if not search_results.empty:
                        st.dataframe(search_results,  use_container_width=True)
                    else:
                        st.warning('No matching records found.')
                else:
                    st.warning('No inventory data found.')
            st.markdown("---")
            with st.form(key='check_out_form'):
                st.markdown(
                    """
                    <style>
                        @import url('https://fonts.googleapis.com/css2?family=Ubuntu&display=swap');
                        
                        .check-out-form-title {
                            font-family: 'Ubuntu', sans-serif;
                            font-size: 28px;
                            color: #2a2a2a;
                            text-align: center;
                        }
                    </style>
                    <h1 class="check-out-form-title">Check Out Book</h1>
                    <p style="text-align: center;">Fill out the form to check out a book.</p>
                    """, 
                    unsafe_allow_html=True
                )

                isbn = create_scanner_input('checkout_isbn')
                student_name = st.text_input('Patron', value='', key='student_name', placeholder='Enter Name of Student')
                checkout_date = st.date_input('Check Out Date', value=dt.today())

                col1, col2 = st.columns(2)
                with col1:
                    yearLevel = st.selectbox('Year Level', options=['Grade 7', 'Grade 8', 'Grade 9', 'Grade 10', 'Grade 11', 'Grade 12'], index=None)     
                with col2:
                    section = st.text_input('Section', value='', key='section', placeholder='Enter Section')
                    submit_button = st.form_submit_button(label='Check Out Book')
                    st.markdown('')

                if submit_button:
                    if not isbn or not student_name or not yearLevel or not section:
                        st.warning('Please fill out all required fields.')
                    else:
                        if os.path.exists('Database.xlsx'):
                            df = pd.read_excel('Database.xlsx', dtype={'ISBN': str})
                            df['ISBN'] = df['ISBN'].str.strip()
                            
                            matching_books = df[df['ISBN'] == isbn.strip()]
                            
                            if len(matching_books) > 0:
                                book_idx = matching_books.index[0]
                                
                                df = update_book_status(df)
                                if df.at[book_idx, 'Status'] == 'Inactive':
                                    st.error('This book is currently unavailable for checkout.')
                                    st.stop()
                                
                                for col in ['Patron', 'Check Out Dates', 'Year Level', 'Section', 'Status']:
                                    if col not in df.columns:
                                        df[col] = ''


                                formatted_date = checkout_date.strftime('%Y-%m-%d')
                                
                                current_patron = str(df.at[book_idx, 'Patron']) if pd.notna(df.at[book_idx, 'Patron']) else ''
                                current_dates = str(df.at[book_idx, 'Check Out Dates']) if pd.notna(df.at[book_idx, 'Check Out Dates']) else ''
                                current_year = str(df.at[book_idx, 'Year Level']) if pd.notna(df.at[book_idx, 'Year Level']) else ''
                                current_section = str(df.at[book_idx, 'Section']) if pd.notna(df.at[book_idx, 'Section']) else ''
                                
                                if current_patron == '':
                                    df.at[book_idx, 'Patron'] = student_name
                                    df.at[book_idx, 'Check Out Dates'] = formatted_date
                                    df.at[book_idx, 'Year Level'] = yearLevel
                                    df.at[book_idx, 'Section'] = section
                                else:
                                    df.at[book_idx, 'Patron'] = f"{current_patron}, {student_name}"
                                    df.at[book_idx, 'Check Out Dates'] = f"{current_dates}, {formatted_date}"
                                    df.at[book_idx, 'Year Level'] = f"{current_year}, {yearLevel}"
                                    df.at[book_idx, 'Section'] = f"{current_section}, {section}"
                                
                                df = update_book_status(df)
                                df.to_excel('Database.xlsx', index=False)
                                st.success('Book has been checked out successfully.')
                                log_transaction('Check Out', isbn, student_name, yearLevel, section)
        


                            else:
                                st.error('Book not found in inventory.')
                        else:
                            st.error('Inventory database not found.')



        #-------------------------------------------------------- CHECK IN ---------------------------------------------------------------------
        if selected == 'Check In':
            st.subheader('Search for Book to Check In')
            search_term = st.text_input('Search by ISBN or Patron', value='', key='search_term', placeholder='Enter search term')
           
            if search_term:
                if os.path.exists('Database.xlsx'):
                    df = pd.read_excel('Database.xlsx')
                        
                    search_results = df[df.apply(
                        lambda row: search_term.lower() in str(row['ISBN']).lower() or search_term.lower() in str(row['Patron']).lower(), axis=1
                    )]
                        
                    if not search_results.empty:
                        st.dataframe(search_results, use_container_width=True)
                    else:
                        st.warning('No matching records found.')
                else:
                    st.warning('No inventory data found.')
            st.markdown("---")
            with st.form(key='check_in_form'):
                st.markdown(
                    """
                    <style>
                        @import url('https://fonts.googleapis.com/css2?family=Ubuntu&display=swap');
                        
                        .check-in-form-title {
                            font-family: 'Ubuntu', sans-serif;
                            font-size: 28px;
                            color: #2a2a2a;
                            text-align: center;
                        }
                    </style>
                    <h1 class="check-in-form-title">Check In Book</h1>
                    <p style="text-align: center;">Fill out the form to return a book.</p>
                    """, 
                    unsafe_allow_html=True
                )
                
                isbn = create_scanner_input('checkin_isbn')
                student_name = st.text_input('Patron', value='', key='student_name', placeholder='Enter Name of Student')
                date = st.date_input('Date', value=dt.today())
                date = date.strftime('%Y-%m-%d')
                col1, col2 = st.columns(2)
                with col1:
                    yearLevel = st.selectbox('Year Level', options=['Grade 7', 'Grade 8', 'Grade 9', 'Grade 10', 'Grade 11', 'Grade 12'], index=None)


                with col2:
                    section = st.text_input('Section', value='', key='section', placeholder='Enter Section')
                    submit_button = st.form_submit_button(label='Return Book')
                    st.markdown('')

                if submit_button:
                    if not isbn or not student_name or not yearLevel or not section:
                        st.warning('Please fill out all required fields.')
                    else:
                        if os.path.exists('Database.xlsx'):
                            df = pd.read_excel('Database.xlsx', dtype={'ISBN': str})
                            df['ISBN'] = df['ISBN'].str.strip()
                            
                            matching_books = df[df['ISBN'] == isbn.strip()]
                            
                            if len(matching_books) > 0:
                                book_idx = matching_books.index[0]
                                
                                patron_list = str(df.at[book_idx, 'Patron']) if pd.notna(df.at[book_idx, 'Patron']) else ''
                                checkout_list = str(df.at[book_idx, 'Check Out Dates']) if pd.notna(df.at[book_idx, 'Check Out Dates']) else ''
                                year_list = str(df.at[book_idx, 'Year Level']) if pd.notna(df.at[book_idx, 'Year Level']) else ''
                                section_list = str(df.at[book_idx, 'Section']) if pd.notna(df.at[book_idx, 'Section']) else ''
                                
                                if patron_list:
                                    patrons = [p.strip() for p in patron_list.split(',')]
                                    checkouts = [d.strip() for d in checkout_list.split(',')]
                                    years = [y.strip() for y in year_list.split(',')] if year_list else []
                                    sections = [s.strip() for s in section_list.split(',')] if section_list else []
                                    
                                    if student_name in patrons:
                                        idx = patrons.index(student_name)
                                        
                                        patrons.pop(idx)
                                        checkouts.pop(idx)
                                        if idx < len(years):
                                            years.pop(idx)
                                        if idx < len(sections):
                                            sections.pop(idx)
                                        
                                        df.at[book_idx, 'Patron'] = ', '.join(patrons) if patrons else ''
                                        df.at[book_idx, 'Check Out Dates'] = ', '.join(checkouts) if checkouts else ''
                                        df.at[book_idx, 'Year Level'] = ', '.join(years) if years else ''
                                        df.at[book_idx, 'Section'] = ', '.join(sections) if sections else ''
                                        
                                        # Update status after modifying data
                                        df = update_book_status(df)
                                        df.to_excel('Database.xlsx', index=False)
                                        st.success('Book has been checked in successfully.')
                                        log_transaction('Check In', isbn, student_name, yearLevel, section)
                                    else:
                                        st.error('The patron name does not match the record.')
                                else:
                                    st.error('No patron found for this book.')
                            else:
                                st.error('Book not found in inventory.')
                        else:
                            st.error('Inventory database not found.')



        #-------------------------------------------------------- RECORD ------------------------------------------------------------------------

        if selected == 'Record':

            record_data = pd.read_excel('Database.xlsx')
            total_books = int(record_data['Quantity'].sum()) 
            borrow_books = int(record_data['Check Out Dates'].apply(count_borrowed_books).sum())  
            available_books = total_books - borrow_books

            valid_book_types = ['Literature', 'Textbooks', 'Journal', 'Research Paper']
            df_book_types = record_data[record_data['Type'].isin(valid_book_types)]
            book_counts = df_book_types.groupby('Type')['Quantity'].sum().reset_index()
            df_book_categories = record_data[record_data['Category'].notnull()]
            book_categories = df_book_categories.groupby('Category')['Quantity'].sum()
            df_cat = book_categories.reset_index()

            col = st.columns([1, 5, 5, 5, 1]  , gap='small')
            st.markdown(
                """
                <head>
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
                </head>
                """, 
                unsafe_allow_html=True
            )


            with col[1]:

                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, #ffffff 0%, #dcffff  100%);
                                width: 80%;
                                padding: 1rem; 
                                border-radius: 0.5rem; 
                                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); 
                                text-align: center;">
                        <h3 style="font-size: 2rem; color: #001f54; "><i class="fa fa-book" style="margin-right: 10px; font-size: 2rem; color: #001f54;"></i>Number of Books</h3>
                        <p style="font-size: 4rem; font-weight: bold;">{total_books}</p>
                        <p style="font-size: 1rem;">Total Number of Books in the Library</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                                
            with col[2]:
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, #ffffff 0%, #dcffff  100%);
                                width: 80%;
                                padding: 1rem; 
                                border-radius: 0.5rem; 
                                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); 
                                text-align: center;">
                        <h3 style="font-size: 2rem; color: #001f54;"><i class="fa fa-bookmark" style="margin-right: 10px; font-size: 2rem; color: #001f54;"></i>Books Borrowed</h3>
                        <p style="font-size: 4rem; font-weight: bold;">{borrow_books}</p>
                        <p style="font-size: 1rem;">Total Borrowed Books in the Library</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

            with col[3]:
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, #ffffff 0%, #dcffff 100%);
                                width: 80%;
                                padding: 1rem; 
                                border-radius: 0.5rem; 
                                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); 
                                text-align: center;">
                        <h3 style="font-size: 2rem; color: #001f54;"><i class="fa fa-book-open" style="margin-right: 10px; font-size: 2rem; color: #001f54;"></i>Available Books</h3>
                        <p style="font-size: 4rem; font-weight: bold;">{available_books}</p>
                        <p style="font-size: 1rem;">Total Available Books in the Library</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            st.markdown('')

            st.markdown('----')


            


            col1, col2, col3 = st.columns([5, 0.5, 5])
            with col1:
                if not book_counts.empty:                  
                    fig = px.pie(book_counts, 
                                names='Type', 
                                values='Quantity', 
                                color='Type',
                                template='plotly',
                                hole=0.2,
                                color_discrete_map={
                                    'Literature': '#282828', 
                                    'Textbooks': '#5c7829', 
                                    'Journal': '#cc3333',
                                    'Research Paper': '#087099'
                                    })

                    fig.update_traces(textinfo='percent+label', pull=[0.1, 0.1, 0.1, 0.1])  

                    fig.update_layout(
                        plot_bgcolor='rgba(0, 0, 0, 0)', 
                        paper_bgcolor='rgba(0, 0, 0, 0)',  
                        title='Distribution of Books by Type',
                        title_x=0.2,
                        title_y=0.05,
                        title_yanchor='bottom',
                        title_font=dict(
                            color='#162938',  
                            size=30
                            )
                        )
                    st.plotly_chart(fig)
                else:
                    st.warning('No data found for book types.')

            with col3:
                if not df_cat.empty:
                    fig = px.bar(df_cat, 
                                x='Category',  
                                y='Quantity',  
                                color='Category',  
                                template='plotly',
                                color_discrete_map={
                                    'Fiction': '#DCB665', 
                                    'Mathematics': '#1380B6', 
                                    'Science': '#ACDF87',
                                    'Social Studies': '#588157',
                                    'Literature and Language Arts': '#344E40',
                                    'Technology and Computer Science': '#CD7672',
                                    'Health and Physical Education': '#0A5C36',
                                    'Art and Music': '#14452F',
                                    'Psychology and Philosophy': '#534666',
                                    'General Studies': '#A3B18A'
                                    })

                    fig.update_layout(
                        plot_bgcolor='rgba(0, 0, 0, 0)',  
                        paper_bgcolor='rgba(0, 0, 0, 0)', 
                        title='Distribution of Books by Category',
                        xaxis_title='',  
                        yaxis_title='', 
                        title_x=0.2,
                        title_y=0.05,
                        title_yanchor='bottom',
                        title_font=dict(
                            color='#162938',  
                            size=30
                        ),
                        xaxis=dict(
                        title=None,  
                        tickfont=dict(color='white')  
                        )

                        )
                        
                                        

                    st.plotly_chart(fig)
                else:
                    st.warning('No data found for book categories.')
            
            user_log_file = 'User.xlsx'
            user_data = pd.read_excel(user_log_file)
            user_data['Date'] = pd.to_datetime(user_data['Date'])
            daily_user_counts = user_data.groupby('Date').size().reset_index(name='User Count')

            if not daily_user_counts.empty:
                    
                fig = px.line(
                    daily_user_counts,
                    x='Date',
                    y='User Count',
                    labels={'Date': 'Date', 'User Count': 'Number of Users'},
                    template='plotly_dark',
                    )
                            
                fig.update_traces(
                    line_color='#FF3333', 
                    line_width=3, 
                    mode='lines+markers', 
                    marker=dict(size=8, color='#FF3333') 
                    )
                fig.update_layout(
                    plot_bgcolor='rgba(0, 0, 0, 0)', 
                    paper_bgcolor='rgba(0, 0, 0, 0)',  
                    title='Daily User Count',
                    title_x=0.4,
                    title_y=0.005,
                    title_yanchor='bottom',
                    title_font=dict(
                        color='#162938',  
                        size=30
                    ),
                    xaxis=dict(
                        title=None,  
                        tickfont=dict(color='white')  
                        ),                 
                    yaxis=dict(
                        title=None,  
                        tickfont=dict(color='white')  
                        )
                    )
                                        
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.warning('No user log data found.')

                
            st.markdown('----')



            tab = st.tabs(['Books', 'Users', 'Transaction'])



            with tab[0]:
                st.subheader('Find Book by Filter')
                inventory_data = pd.read_excel('Database.xlsx')
                col1, col2 = st.columns(2)
                with col1:
                    sub_col = st.columns(2)
                    with sub_col[0]:
                        selected_types = st.multiselect(
                            'Filter by Type:',
                            inventory_data['Type'].unique().tolist()
                            )
                        
                    with sub_col[1]:
                        selected_categories = st.multiselect(
                            'Filter by Category:',
                            inventory_data['Category'].unique().tolist()
                        )

                    if selected_types or selected_categories:
                        mask = pd.Series(True, index=inventory_data.index)

                    if selected_types:
                        mask &= inventory_data['Type'].isin(selected_types)
                        
                    if selected_categories:
                        mask &= inventory_data['Category'].isin(selected_categories)
                        
                        filtered_data = inventory_data[mask]
                        st.dataframe(filtered_data, use_container_width=True)
                    else:
                        st.write("Select filters to view the data.")

            with tab[1]:
                col1, col2 = st.columns(2)
                with col1:
                    user_log_data = pd.read_excel('User.xlsx')
                    st.subheader('Find User by Filter')
                    sub_col = st.columns(2)
                    with sub_col[0]:
                        selected_types = st.multiselect(
                            'Filter by Year Level:',
                            user_log_data['Year Level'].unique().tolist()
                            )
                        
                    with sub_col[1]:
                        selected_categories = st.multiselect(
                            'Filter by Section:',
                            user_log_data['Section'].unique().tolist()
                        )

                    if selected_types or selected_categories:
                        mask = pd.Series(True, index=user_log_data.index)

                    if selected_types:
                        mask &= user_log_data['Year Level'].isin(selected_types)
                        
                    if selected_categories:
                        mask &= user_log_data['Section'].isin(selected_categories)
                        
                        filtered_data = user_log_data[mask]
                        st.dataframe(filtered_data, use_container_width=True)
                    else:
                        st.write("Select filters to view the data.")

                with st.expander('Download User Log'):
                        try:
                            user_data = pd.read_excel('User.xlsx')
                            edited_user_data = st.data_editor(
                                user_data,
                                key="user_editor",
                                use_container_width=True
                            )
                            
                            if st.button("Save Changes", key="save_user"):
                                try:

                                    edited_user_data.to_excel('User.xlsx', index=False)
                                    st.success("Changes saved successfully!")
                                except Exception as e:
                                    st.error(f"Error saving changes: {e}")
                        except Exception as e:
                            st.error(f"Error loading user data: {e}")

            with tab[2]:

                transaction_data = pd.read_excel('Transaction.xlsx')
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader('Find User by Filter')
                    sub_col = st.columns(2)
                    with sub_col[0]:
                        selected_types = st.multiselect(
                            'Filter by Transaction Type:',
                            transaction_data['Transaction Type'].unique().tolist()
                            )
                        
                    if selected_types or selected_categories:
                        mask = pd.Series(True, index=transaction_data.index)

                    if selected_types:
                        mask &= transaction_data['Transaction Type'].isin(selected_types)

                        filtered_data = transaction_data[mask]
                        st.dataframe(filtered_data, use_container_width=True)
                    else:
                        st.write("Select filters to view the data.")
                   
                with st.expander( 'Transaction Log'):
                        try:
                            transaction_data = pd.read_excel('Transaction.xlsx')
                            edited_transaction_data = st.data_editor(
                                transaction_data,
                                key="transaction_editor",
                                use_container_width=True
                            )
                            
                            if st.button("Save Changes", key="save_transaction"):
                                try:

                                    edited_transaction_data.to_excel('Transaction.xlsx', index=False)
                                    st.success("Changes saved successfully!")
                                except Exception as e:
                                    st.error(f"Error saving changes: {e}")
                        except Exception as e:
                            st.error(f"Error loading transaction data: {e}")
    #-------------------------------------------------------- OTHER ------------------------------------------------------------------------


        if selected == 'Log Form':
            st.title('')
            other_file_name = 'User.xlsx'
            try:
                user_data = pd.read_excel(other_file_name)
            except FileNotFoundError:
                user_data = pd.DataFrame(columns=["Date", "Patron", "Year Level", "Section", "Purpose"])
            with st.form(key='other_form'):
                st.markdown(
                    """
                    <style>
                        @import url('https://fonts.googleapis.com/css2?family=Ubuntu&display=swap');
                    
                        .other-title {
                            font-family: 'Ubuntu', sans-serif;
                            font-size: 28px;
                            color: #2a2a2a;
                            text-align: center;
                        }
                    </style>
                    <h1 class="other-title">User Log Form</h1>
                    <p style="text-align: center;">Fill out the form.</p>
                    """, 
                    unsafe_allow_html=True
                )
                studentName = st.text_input('Patron', value='', key='student_name', placeholder='Enter Name of Student')
                date = st.date_input('Date', value=dt.today())
                date = date.strftime('%Y-%m-%d')  

                    
                col1, col2 = st.columns(2, gap='small')
                with col1:
                    yearLevel = st.selectbox('Year Level', options=['Grade 7', 'Grade 8', 'Grade 9', 'Grade 10', 'Grade 11', 'Grade 12'], index=None)
                    purpose = st.toggle('Will borrow book', key='purpose', value=False)
                    purpose_value = 'Borrow book' if purpose else 'Read'
                with col2:
                    section = st.text_input('Section', value='', key='section', placeholder='Enter Section')
                    st.markdown('')
                    submit_button = st.form_submit_button(label='**Submit**')




                st.markdown('')

                if submit_button:
                    new_data = {
                        "Date": date,
                        "Patron": studentName,
                        "Year Level": yearLevel,
                        "Section": section,
                        "Purpose": purpose_value
                    }

                    new_data_df = pd.DataFrame([new_data])
                    user_data = pd.concat([user_data, new_data_df], ignore_index=True)
                    user_data.to_excel(other_file_name, index=False)
                    st.success('Form submitted successfully!')


        if selected == 'Sign Out':
            st.session_state.password_correct = False
            st.rerun()

    def main():
        dashboard()

    if __name__ == '__main__':
        main()

