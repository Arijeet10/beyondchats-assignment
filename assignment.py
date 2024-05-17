import tkinter as tk
from tkinter import scrolledtext, Listbox, END, SINGLE
import requests
from threading import Thread
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_data_from_api(url):
    """Fetch data from the API.

    Args:
        url (str): The API endpoint URL.

    Returns:
        dict or str: The parsed JSON data from the API or an error message.
    """
    try:
        response = requests.get(url, timeout=30)  # increased timeout to 30 seconds
        response.raise_for_status()  # raised an error for bad status codes
        data = response.json()  # parsed JSON data
        return data
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err}"
    except requests.exceptions.RequestException as err:
        return f"An error occurred: {err}"
    except ValueError:
        return "Error parsing JSON response"

def identify_sources(data):
    """Identify the sources for each message.

    Args:
        data (list): A list of dictionaries containing messages and sources.

    Returns:
        list: A list of lists containing sources for each message.
    """
    citations = []
    for item in data:
        message = item.get('message', '')
        sources = item.get('sources', [])
        message_citations = [source for source in sources if source in message]
        citations.append(message_citations)
    return citations

def fetch_and_display_data():
    """Fetch data from the API and display it in the Listbox and Text widget."""
    def run():
        api_url = "https://devapi.beyondchats.com/api/get_message_with_sources"
        data = get_data_from_api(api_url)
        if isinstance(data, list):
            citations = identify_sources(data)
            display_data(data, citations)  # displaying data and citations
        else:
            display_error(data)  # displaying error message
        fetch_button.config(state=tk.NORMAL)  # re-enable the fetch button
        loading_label.pack_forget()  # hiding loading label

    fetch_button.config(state=tk.DISABLED)  # disabling the fetch button
    loading_label.pack()  # show loading label

    # Run the API request in a separate thread
    thread = Thread(target=run)
    thread.start()

def display_data(data, citations):
    """Display the messages in the Listbox and store their citations.

    Args:
        data (list): The list of messages.
        citations (list): The list of citations for each message.
    """
    message_listbox.delete(0, END)  # clearing the listbox
    for index, item in enumerate(data):
        message_listbox.insert(END, f"Message {index + 1}")  # inserting messages into the Listbox

    # storing citations in a global variable for later access
    global message_citations
    message_citations = citations

def display_error(error_message):
    """Display an error message in the Text widget.

    Args:
        error_message (str): The error message to display.
    """
    text_area.config(state=tk.NORMAL)
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.INSERT, error_message)
    text_area.config(state=tk.DISABLED)

def on_message_select(event):
    """Display the citations for the selected message in the Text widget.

    Args:
        event (tk.Event): The event that triggered this function.
    """
    selected_index = message_listbox.curselection()
    if selected_index:
        index = selected_index[0]
        citations = message_citations[index]
        text_area.config(state=tk.NORMAL)
        text_area.delete(1.0, tk.END)
        if citations:
            text_area.insert(tk.INSERT, "\n".join(citations))  # display citations
        else:
            text_area.insert(tk.INSERT, "No citations found.")  # display no citations found message
        text_area.config(state=tk.DISABLED)

# setting up the main application window
root = tk.Tk()
root.title("API Data Fetcher")

# setting up a button to fetch data
fetch_button = tk.Button(root, text="Fetch Data", command=fetch_and_display_data)
fetch_button.pack(pady=10)

# setting up a label for showing loading message
loading_label = tk.Label(root, text="API Request!!Loading...", fg="red")

# setting up a listbox to display messages
message_listbox = Listbox(root, width=80, height=10, selectmode=SINGLE)
message_listbox.pack(padx=10, pady=10)
message_listbox.bind('<<ListboxSelect>>', on_message_select)  # Bind the select event to a function

# setting up a scrolled text area to display the citations
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=10, state=tk.DISABLED)
text_area.pack(padx=10, pady=10)

# global variable to store citations
message_citations = []

# starting the GUI event loop
root.mainloop()
