import streamlit as st
import json
import datetime
from dotenv import load_dotenv, find_dotenv
import os
from crewai import LLM
from crewai_tools import SerperDevTool, \
                         ScrapeWebsiteTool, \
                         WebsiteSearchTool


def append_crewai_output_to_history(
    file_path: str,  
    crew_output: str,
    event: str,
    location: str,
    budget: str,
    
):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    crew_output = str(crew_output)
    
    entry = {
        
        "timestamp": timestamp,
        "event":event,
        "location":location,
        "budget":budget,
        "output": crew_output,
        
        
    }
    
    history_data = []
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            if not isinstance(history_data, list): # Ensure it's a list
                history_data = []
        except json.JSONDecodeError:
            print(f"Warning: Existing file '{file_path}' is not valid JSON. Starting new history.")
            history_data = []
    
    history_data.append(entry)

   
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, indent=2, ensure_ascii=False)

    print(f"CrewAI output appended to '{file_path}'.")
def get_file_extension(file_path):
    return os.path.splitext(file_path)[1].lower()
def display_text_content_natural_scroll(file_path):
    """Displays text-based content, allowing natural page scrolling."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        file_ext = get_file_extension(file_path)
        
        if file_ext == ".md":
            st.markdown(content) 
        elif file_ext == ".py":
            st.code(content, language="python") # Displays code with syntax highlighting
        elif file_ext == ".json":
            
            st.sidebar.write("Chat History")
            st.sidebar.json(json.loads(content)) # Attempt to parse and display formatted JSON
        else: 
            st.text(content)
            
    except FileNotFoundError:
        st.error(f"Error: File not found at '{file_path}'")
    except json.JSONDecodeError as e:
        st.error(f"Error: Could not parse JSON file '{file_path}'. Invalid JSON format: {e}")
        st.code(content, language="json") # Show raw if parsing fails
    except Exception as e:
        st.error(f"Error reading text file '{file_path}': {e}")
def load_env():
    _ = load_dotenv(find_dotenv())
def get_serper_api_key():
    load_env()
    serper_api_key = os.getenv("SERPER_API_KEY")
    if not serper_api_key:
        raise ValueError("SERPER_API_KEY is not set")
    return serper_api_key
def get_gemini_api_key():
    load_env()
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not set")
    return gemini_api_key
def pretty_print_result(result):
  parsed_result = []
  for line in result.split('\n'):
      if len(line) > 80:
          words = line.split(' ')
          new_line = ''
          for word in words:
              if len(new_line) + len(word) + 1 > 80:
                  parsed_result.append(new_line)
                  new_line = word
              else:
                  if new_line == '':
                      new_line = word
                  else:
                      new_line += ' ' + word
          parsed_result.append(new_line)
      else:
          parsed_result.append(line)
  return "\n".join(parsed_result)

import warnings
warnings.filterwarnings('ignore')
from crewai import Agent, Task, Crew
with open(".env", "w") as f:
    f.write("GEMINI_API_KEY=Your key here\n")
with open(".env", "w") as f:
    f.write("SERPER_API_KEY=Your key here\n")
import os
os.environ["GEMINI_API_KEY"] = "Your key here"
gemini_api_key = get_gemini_api_key()
gemini_llm = LLM(
    provider="gemini",
    model="gemini/gemini-2.5-flash",  # Or gemini/gemini-2.0-flash-thinking
    api_key=gemini_api_key,
)
serper_api_key=get_serper_api_key()
yaml_config = """
model_list:
  - model_name: gemini/gemini-2.5-flash
    litellm_provider: gemini
    api_key: "${Your key here}"
"""

with open("litellm.yaml", "w") as f:
    f.write(yaml_config)
import litellm
litellm._turn_on_debug()


gemini_llm = LLM(model="gemini/gemini-2.5-flash") 
history="chat.json" 
Serper_Dev_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()
st.set_page_config(page_title="Event Planner - CrewAI", page_icon="🧠")
st.title("Plan Your Event with CrewAI Agents")
st.markdown("Fill out the form below to generate an event plan:")
event_coordinator = Agent(
    role='Event Coordinator',
    goal='Oversee the complete event planning process for {event} from conception to execution at a location {location}',
    backstory=(
        "With over a decade of experience in planning corporate summits, weddings, and international expos, "
        "You are a seasoned event strategist known for bringing order to chaos. Armed with project management "
        "certifications, calendar mastery, and unmatched multitasking skills, you have successfully handled high-stress "
        "events with thousands of guests. your superpower is attention to detail, ensuring every element—no matter how small—"
        "aligns perfectly with the event’s theme and timeline. Driven by the thrill of flawless execution and client satisfaction, "
        "you act as the control tower ensuring every team member is in sync."
        "make sure your plans are in the budget of {budget}, which is specified by your customer"
        "You adjust the timing of all events in {event} and also suggest a suitable time to start {event}"
        "Make sure to include the timeline in the final output and document"
        "Make the document as detailed as possible"
    ),
    verbose=True,
    llm=gemini_llm,
    allow_delegation=True
)
venue_logistics_agent = Agent(
    role='Venue & Logistics Manager',
    goal='Source the perfect venue and manage all logistical details such as layout, lighting, transportation, and equipment setup for {event}',
    backstory=(
        "You are a former operations director at a global hotel chain, this agent has negotiated and inspected hundreds of venues "
        "across continents. You are known for Your uncanny ability to visualize spatial layouts and foresee potential logistical "
        "issues before they arise. From load-in/load-out schedules to emergency exits, you ensure every technical and operational "
        "aspect runs like a well-oiled machine. Adept with CAD layouts, transportation logistics, and vendor coordination, "
        "you take pride in transforming blank spaces into stunning, functional environments."
        "make sure your plans are in the budget of {budget}, which is specified by your customer"
        "make sure to also take the distance factor from {location} where {event} is held while planning"
        "Make sure to add venue details in the final document"
        "Make sure to include vendor for equipment and venue details in the final document and output"
        "Make the document as detailed as possible not missing any  info"
    ),
    verbose=True,
    llm=gemini_llm,
    tools = [scrape_tool, Serper_Dev_tool]
)
catering_agent = Agent(
    role='Catering & Menu Specialist',
    goal='Plan and organize food, drinks, and catering vendors tailored to the event theme and guest preferences',
    backstory=(
        "Once a sous-chef turned event culinary consultant, you blend gastronomic creativity with practical experience. "
        "You have curated menus for celebrity galas, cultural festivals, and high-end corporate events. With a deep understanding of "
        "dietary restrictions, food allergies, and plating aesthetics, you ensure that each dish is both safe and memorable. "
        "Your network includes top-tier caterers, mixologists, and specialty vendors, and their mission is to turn food into a "
        "conversation starter at every event."
        "make sure your plans are in the budget of {budget}, which is specified by your customer"
        "make sure to also take the distance factor from {location} where {event} is held while planning"
        "Choose the right caterers"
        "add all the important details in the form of list in the document"
        "Make the document as detailed as possible"
    ),
    verbose=True,
    llm=gemini_llm,
    tools = [scrape_tool, Serper_Dev_tool]
)
entertainment_agent = Agent(
    role='Entertainment & Guest Engagement Planner',
    goal='Select suitable entertainment and manage schedules to keep guests engaged throughout the event',
    backstory=(
        "You are former talent agent with a background in performing arts and show production, you know exactly how to light up a room. "
        "You have access to a global roster of musicians, comedians, keynote speakers, and interactive performers. Beyond stage acts, "
        "You also design personalized engagement experiences such as photo booths, games, and virtual integrations. Whether it's a tech "
        "conference or a boho wedding, their goal is to make guests leave with smiles, memories, and Instagram stories worth sharing."
        "make sure your plans are in the budget of {budget}, which is specified by your customer"
        "make sure to also take the distance factor from {location} where {event} is held while planning"
        "Make the document as detailed as possible with all neccessary info"
        "make sure to include Schedule Recommendations for Entertainment & Engagement"
    ),
    verbose=True,
    llm=gemini_llm,
    tools = [scrape_tool, Serper_Dev_tool]
)
budget_agent = Agent(
    role='Budget & Vendor Manager',
    goal='Manage finances, negotiate vendor deals, and ensure the {event} stays within budget as given as input by the user, and the budget is {budget}',
    backstory=(
        "Previously a procurement specialist at a multinational event production firm, you combine negotiation skills "
        "with financial analytics to deliver cost-effective yet premium results. You known for squeezing value out of every dollar "
        "and establishing win-win vendor relationships. Fluent in spreadsheets and contracts, you are also skilled at tracking real-time "
        "expenditures, predicting overages, and generating financial reports post-event. Their motto: 'Big impact, controlled spend.'And your goal is to make the {event} a sucess using your skills mentioned above"
        "You have to tell the other agents working with you to change their output if you feel that their plan is not in the {budget} of the {event} which is to be conducted"
        "make sure to also take the distance factor from {location} where {event} is held while planning"
    ),
    verbose=True,
    llm=gemini_llm,
    tools = [scrape_tool, Serper_Dev_tool],
    allow_delegation=True
)
shared_output_file = "event_plan.txt"

coordination_task = Task(
    description="Outline the high-level agenda and event timeline including milestones and key decision points.",
    expected_output="Add the agenda and event timeline to the shared event plan document.",
    agent=event_coordinator,

    output_file=shared_output_file,
    human_input=False,
)
logistics_task = Task(
    description="Research and propose 2-3 venue options with layout details, location pros/cons, and logistic requirements.",
    expected_output="Append venue details, transportation logistics, and equipment needs to the event plan,and other important details.Add all the details  in the document",
    agent=venue_logistics_agent,

    output_file=shared_output_file,
    human_input=False,
)
catering_task = Task(
    description="Design a sample menu for the event, listing appetizers, mains, desserts, and drinks for various dietary needs.",
    expected_output="Add the catering plan and list of potential vendors to the shared document.Add details for each vendor like the amount caterer will take, and what is included in menu.",
    agent=catering_agent,

    output_file=shared_output_file,
    human_input=False,
)
entertainment_task = Task(
    description="Propose entertainment options including performers, guest interaction ideas, and schedule recommendations.",
    expected_output="Write the entertainment plan section of the event file.",
    agent=entertainment_agent,
    output_file=shared_output_file,
    human_input=False,
)
budget_task = Task(
    description="Estimate the cost breakdown for venue, catering, entertainment, staffing, and contingency.",
    expected_output="Include the budget table and notes on cost-saving strategies in the document.",
    agent=budget_agent,
    output_file=shared_output_file,
    human_input=False,
)

Crew=Crew(
    agents=[
        event_coordinator,
        venue_logistics_agent,
        catering_agent,
        entertainment_agent,
        budget_agent
    ],
    tasks=[
        coordination_task,
        logistics_task,
        catering_task,
        entertainment_task,
        budget_task
    ],
    llm=gemini_llm,
    verbose=True
)

display_text_content_natural_scroll(history)
with st.form("event_form"):
    event_name = st.text_input("📝 Event Name", placeholder="Event Name")
    location = st.text_input("📍 Location", placeholder="Location")
    budget = st.number_input("💰 Budget (INR)", min_value=1000, step=1000, value=200000)
    submitted = st.form_submit_button("🚀 Generate Event Plan")
details={
    'event':event_name,
    'location':location,
    'budget':budget

}
if submitted:
    with st.spinner("Running CrewAI agents..."):

      result=Crew.kickoff(inputs=details)
    st.success("✅ Event Plan Generated!")
    st.write("### 🧾 Full Event Plan:")
    
    with open("event_plan.txt", "r") as file:
        file_content = file.read()
        st.download_button("📥 Download Plan", file_content, file_name="event_plan.txt")
        st.write(file_content)
        append_crewai_output_to_history(history,result,details["event"],details["location"],details["budget"]  )
        
