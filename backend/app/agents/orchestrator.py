from guard_agent import guard_agent
from router_agent import detect_intent
from lawyer_agent import lawyer_agent
from form_agent import form_agent

def orchestrator(question: str, country: str = "thailand"):
    if not guard_agent(question):
        return "Запрос не относится к теме поездок и въезда."
    intent = detect_intent(question)
    
    responses = []
    
    if intent in ["LAW", "BOTH"]:
        lawyer_response = lawyer_agent(question)
        responses.append(lawyer_response)
    
    if intent in ["FORM", "BOTH"]:
        form_response = form_agent(country, question)
        responses.append(form_response)
    
    final_response = "\n\n---\n\n".join(responses)
    return final_response