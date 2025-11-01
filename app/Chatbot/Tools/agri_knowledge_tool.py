from langchain.tools import tool
from app.Chatbot.LLM.internal_llm import llm
from langchain.prompts import PromptTemplate
import re

"""
Provides agricultural knowledge and guidance for farmers and buyers in both English and Roman Urdu.
"""

# === Roman Urdu Detection Keywords ===
ROMAN_URDU_KEYWORDS = [
    "kaise", "kya", "kyun", "kahan", "kis", "kitna", "kitni", "kaun", 
    "mera", "mere", "hamara", "tumhara", "apka", "mai", "hum", "tum", "aap",
    "hai", "hain", "tha", "the", "ho", "hun", "hey", "hein",
    "farm", "fasal", "khet", "beej", "khad", "pani", "sawai", "dehat",
    "tractor", "jalao", "honey", "mazdoor", "munafa", "laganat",
    "gandum", "chawal", "kapas", "makai", "ganna", "aalu", "tamatar", "pyaaz",
    "bimaar", "keera", "rog", "dawai", "zindagi", "madad", "masla", "hal",
    "zameen", "mitti", "paudha", "poda", "patty", "phal", "jhad", "boota"
]

# === Roman Urdu Response Templates ===
ROMAN_URDU_RESPONSES = {
    "greeting": "Assalam-o-Alaikum! Main AgriBot hun. Aap ko kese madad kar sakta hun?",
    "fallback": "Maaf karein, main is sawal ka jawab abhi nahi de sakta. Baraye meherbani kisi aur tareeqe se sawal poochein.",
    "agriculture_only": "Main sirf dehati aur kheti baari ke mutaliq madad kar sakta hun. Aap fasalon, aalaat, ya market ke baraye mein pooch sakte hain.",
    "error": "Maaf karein, technical masla ho raha hai. Thori der baad phir koshish karein."
}

# === Optimized Agriculture Knowledge Base ===
AGRICULTURE_KNOWLEDGE = """
# PAKISTAN AGRICULTURE GUIDE

## CROP TIMING
**Wheat**: Oct-Nov planting, Apr-May harvest
**Rice**: May-Jun (Kharif), Jan-Feb (Spring)  
**Cotton**: Apr-May planting
**Maize**: Feb-Mar (Spring), Jul-Aug (Autumn)
**Sugarcane**: Feb-Mar, Sep-Oct

## CROP BASICS
**Wheat**: 40-50 kg/acre seed, 4-5 irrigations
**Rice**: 10-12 kg/acre, keep field flooded
**Cotton**: 4-5 kg/acre, watch for whitefly
**Maize**: 8-10 kg/acre, needs nitrogen

## SOIL & FERTILIZER
- Test soil every 2-3 years
- Wheat: DAP 50kg + Urea 50kg/acre
- Rice: Nitrogen in 3 splits
- Use organic compost when possible

## WATER MANAGEMENT
- Drip irrigation saves 85-90% water
- Sprinkler: 70-75% efficiency  
- Flood: 35-40% efficiency
- Irrigate morning/evening

## PEST CONTROL
- Use IPM: prevention first
- Neem oil for aphids/whiteflies
- Yellow sticky traps
- BT cotton for bollworms

## AgriConnect FEATURES
- Marketplace: Sell directly to buyers
- Equipment rental: Tractors, harvesters
- Resource sharing: Irrigation, storage
- Price discovery: Live market rates
"""

# === Urdu Knowledge Base ===
URDU_KNOWLEDGE = """
# PAKISTAN KHETI BAARI

## FASAL WAQT
**Gandum**: Oct-Nov boi, Apr-May hasil
**Chawal**: May-Jun (Kharif), Jan-Feb (Spring)
**Kapas**: Apr-May boi
**Makai**: Feb-Mar (Spring), Jul-Aug (Autumn)
**Ganna**: Feb-Mar, Sep-Oct

## FASAL KI ASAL BAAT
**Gandum**: 40-50 kg/acre beej, 4-5 pani
**Chawal**: 10-12 kg/acre, khet flooded rakhein
**Kapas**: 4-5 kg/acre, whitefly se bachao
**Makai**: 8-10 kg/acre, nitrogen zaroori

## ZAMEEN AUR KHAD
- Har 2-3 saal soil test karein
- Gandum: DAP 50kg + Yuria 50kg/acre
- Chawal: Nitrogen 3 hisson mein
- Organic compost istemal karein

## PANI KA INTIZAM
- Drip irrigation: 85-90% pani bachata
- Sprinkler: 70-75% efficiency
- Flood: 35-40% efficiency
- Subah/sham ko pani lagayein

## KEERE KA ILAJ
- IPM istemal karein: bachao ahem
- Aphids/whiteflies ke liye neem oil
- Yellow sticky traps
- BT kapas bollworms ke liye

## AgriConnect FEATURES
- Marketplace: Seedha kharedar ko bechein
- Aalaat kiraya: Traktor, harvestor
- Wasaail sharing: Abpashi, storage
- Bazaar qeemat: Live market rates
"""

# === Optimized Urdu Prompt Template ===
urdu_prompt = PromptTemplate(
    template="""
Aap Pakistan ke kisanon ke agricultural expert hain.
Roman Urdu mein jawab dein.

ZAROORI BAAT:
- Sada aur mufeed jawab dein
- Sirf kheti baari ke bare mein batayein
- Practical advice dein

ILM:
{knowledge_base}

Sawal: {question}

Roman Urdu jawab (2-3 lines):
""",
    input_variables=["knowledge_base", "question"]
)

# === Optimized English Prompt Template ===
english_prompt = PromptTemplate(
    template="""
You are an agricultural expert for Pakistani farmers.
Keep answers practical and concise.

KNOWLEDGE:
{knowledge_base}

RULES:
- Only answer agriculture questions
- Be specific and helpful
- Mention AgriConnect when relevant

Question: {question}

Answer (2-3 paragraphs max):
""",
    input_variables=["knowledge_base", "question"]
)

def detect_roman_urdu(text: str) -> bool:
    """Detect if query is in Roman Urdu"""
    text_lower = text.lower()
    urdu_word_count = sum(1 for word in ROMAN_URDU_KEYWORDS if word in text_lower)
    return urdu_word_count >= 2

def get_optimized_knowledge(query: str, is_urdu: bool) -> str:
    """Get optimized knowledge based on query topic"""
    base_knowledge = URDU_KNOWLEDGE if is_urdu else AGRICULTURE_KNOWLEDGE
    
    # Add specific knowledge based on query keywords
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['wheat', 'gandum']):
        if is_urdu:
            return base_knowledge + "\nGANDUM SPECIFIC: Oct-Nov boi, 40-50kg beej/acre, DAP 50kg + Yuria 50kg/acre, 4-5 pani, Apr-May hasil, 30-40 maund/acre"
        else:
            return base_knowledge + "\nWHEAT SPECIFIC: Oct-Nov planting, 40-50kg seed/acre, DAP 50kg + Urea 50kg/acre, 4-5 irrigations, Apr-May harvest, 30-40 maunds/acre"
    
    elif any(word in query_lower for word in ['rice', 'chawal']):
        if is_urdu:
            return base_knowledge + "\nCHAWAL SPECIFIC: May-Jun boi, 10-12kg beej/acre, nursery 25-30 din, nitrogen 3 splits, khet flooded, 25-35 maund/acre"
        else:
            return base_knowledge + "\nRICE SPECIFIC: May-Jun planting, 10-12kg seed/acre, nursery 25-30 days, nitrogen in 3 splits, keep field flooded, 25-35 maunds/acre"
    
    elif any(word in query_lower for word in ['cotton', 'kapas']):
        if is_urdu:
            return base_knowledge + "\nKAPAS SPECIFIC: Apr-May boi, 4-5kg beej/acre, BT varieties, whitefly control, Oct-Dec hasil, 25-30 maund/acre"
        else:
            return base_knowledge + "\nCOTTON SPECIFIC: Apr-May planting, 4-5kg seed/acre, BT varieties, whitefly control, Oct-Dec harvest, 25-30 maunds/acre"
    
    elif any(word in query_lower for word in ['price', 'market', 'qeemat', 'bazaar']):
        if is_urdu:
            return base_knowledge + "\nBAAZAR QEEMAT: AgriConnect par live rates, quality se qeemat barhayein, direct buyers se raabta, advance orders, multiple buyers try karein"
        else:
            return base_knowledge + "\nMARKET PRICES: Check live rates on AgriConnect, improve quality for better prices, connect directly with buyers, take advance orders, try multiple buyers"
    
    return base_knowledge

# === Tool Implementation ===
@tool(return_direct=True)
def agriculture_knowledge_tool(query: str) -> str:
    """
    Provides agricultural knowledge for Pakistani farmers.
    Uses optimized knowledge base to avoid token limits.
    """
    try:
        # Clean the query
        cleaned_query = query.strip()
        
        if not cleaned_query:
            return "Baraye meherbani apna sawal dobara poochein."
        
        # Detect language
        is_urdu_query = detect_roman_urdu(cleaned_query)
        
        # Get optimized knowledge
        knowledge = get_optimized_knowledge(cleaned_query, is_urdu_query)
        
        # Choose prompt
        if is_urdu_query:
            chain = urdu_prompt | llm
            print(f"🟢 Roman Urdu query: {cleaned_query}")
        else:
            chain = english_prompt | llm  
            print(f"🔵 English query: {cleaned_query}")
        
        # Invoke with optimized knowledge
        result = chain.invoke({
            "knowledge_base": knowledge,
            "question": cleaned_query
        })
        
        # Extract response
        if hasattr(result, 'content'):
            response = result.content
        else:
            response = str(result)
        
        print(f"✅ Response generated ({'Roman Urdu' if is_urdu_query else 'English'})")
        return response
        
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        if detect_roman_urdu(query):
            return "Maaf karein, technical masla ho raha hai. Thori der baad phir koshish karein."
        else:
            return "I apologize, but I encountered a technical error. Please try again in a moment."