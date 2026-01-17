"""
Indian States and Cities data
Comprehensive list for location-based budget recommendations
"""

INDIAN_STATES_CITIES = {
    "Andhra Pradesh": [
        "Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Kurnool",
        "Kakinada", "Rajahmundry", "Tirupati", "Kadapa", "Anantapur"
    ],
    "Arunachal Pradesh": [
        "Itanagar", "Naharlagun", "Pasighat", "Namsai", "Tawang"
    ],
    "Assam": [
        "Guwahati", "Silchar", "Dibrugarh", "Jorhat", "Nagaon",
        "Tinsukia", "Tezpur", "Bongaigaon", "Dhubri", "Karimganj"
    ],
    "Bihar": [
        "Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Purnia",
        "Darbhanga", "Bihar Sharif", "Arrah", "Begusarai", "Katihar"
    ],
    "Chhattisgarh": [
        "Raipur", "Bhilai", "Bilaspur", "Korba", "Durg",
        "Rajnandgaon", "Raigarh", "Jagdalpur", "Ambikapur"
    ],
    "Goa": [
        "Panaji", "Margao", "Vasco da Gama", "Mapusa", "Ponda"
    ],
    "Gujarat": [
        "Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar",
        "Jamnagar", "Junagadh", "Gandhidham", "Nadiad", "Morbi"
    ],
    "Haryana": [
        "Faridabad", "Gurgaon", "Panipat", "Ambala", "Yamunanagar",
        "Rohtak", "Hisar", "Karnal", "Sonipat", "Panchkula"
    ],
    "Himachal Pradesh": [
        "Shimla", "Dharamshala", "Solan", "Mandi", "Kullu",
        "Hamirpur", "Bilaspur", "Una", "Kangra"
    ],
    "Jharkhand": [
        "Ranchi", "Jamshedpur", "Dhanbad", "Bokaro", "Deoghar",
        "Phusro", "Hazaribagh", "Giridih", "Ramgarh"
    ],
    "Karnataka": [
        "Bangalore", "Mysore", "Mangalore", "Hubli", "Belgaum",
        "Dharwad", "Gulbarga", "Bellary", "Tumkur", "Davanagere"
    ],
    "Kerala": [
        "Thiruvananthapuram", "Kochi", "Kozhikode", "Kollam", "Thrissur",
        "Kannur", "Alappuzha", "Kottayam", "Palakkad", "Malappuram"
    ],
    "Madhya Pradesh": [
        "Indore", "Bhopal", "Jabalpur", "Gwalior", "Ujjain",
        "Sagar", "Dewas", "Satna", "Ratlam", "Rewa"
    ],
    "Maharashtra": [
        "Mumbai", "Pune", "Nagpur", "Thane", "Nashik",
        "Aurangabad", "Solapur", "Kolhapur", "Amravati", "Navi Mumbai"
    ],
    "Manipur": [
        "Imphal", "Thoubal", "Bishnupur", "Churachandpur"
    ],
    "Meghalaya": [
        "Shillong", "Tura", "Nongstoin", "Jowai"
    ],
    "Mizoram": [
        "Aizawl", "Lunglei", "Champhai", "Serchhip"
    ],
    "Nagaland": [
        "Kohima", "Dimapur", "Mokokchung", "Tuensang"
    ],
    "Odisha": [
        "Bhubaneswar", "Cuttack", "Rourkela", "Brahmapur", "Sambalpur",
        "Puri", "Balasore", "Bhadrak", "Baripada"
    ],
    "Punjab": [
        "Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda",
        "Hoshiarpur", "Mohali", "Pathankot", "Moga", "Abohar"
    ],
    "Rajasthan": [
        "Jaipur", "Jodhpur", "Kota", "Bikaner", "Ajmer",
        "Udaipur", "Bhilwara", "Alwar", "Bharatpur", "Sikar"
    ],
    "Sikkim": [
        "Gangtok", "Namchi", "Gyalshing", "Mangan"
    ],
    "Tamil Nadu": [
        "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem",
        "Tirunelveli", "Tiruppur", "Vellore", "Erode", "Thoothukudi"
    ],
    "Telangana": [
        "Hyderabad", "Warangal", "Nizamabad", "Karimnagar", "Khammam",
        "Ramagundam", "Mahbubnagar", "Nalgonda", "Adilabad"
    ],
    "Tripura": [
        "Agartala", "Dharmanagar", "Udaipur", "Kailasahar"
    ],
    "Uttar Pradesh": [
        "Lucknow", "Kanpur", "Ghaziabad", "Agra", "Varanasi",
        "Meerut", "Allahabad", "Bareilly", "Aligarh", "Moradabad"
    ],
    "Uttarakhand": [
        "Dehradun", "Haridwar", "Roorkee", "Haldwani", "Rudrapur",
        "Kashipur", "Rishikesh", "Nainital"
    ],
    "West Bengal": [
        "Kolkata", "Asansol", "Siliguri", "Durgapur", "Bardhaman",
        "Malda", "Baharampur", "Habra", "Kharagpur", "Shantipur"
    ],
    "Andaman and Nicobar Islands": [
        "Port Blair"
    ],
    "Chandigarh": [
        "Chandigarh"
    ],
    "Dadra and Nagar Haveli and Daman and Diu": [
        "Daman", "Diu", "Silvassa"
    ],
    "Delhi": [
        "New Delhi", "North Delhi", "South Delhi", "East Delhi", "West Delhi"
    ],
    "Jammu and Kashmir": [
        "Srinagar", "Jammu", "Anantnag", "Baramulla", "Sopore"
    ],
    "Ladakh": [
        "Leh", "Kargil"
    ],
    "Lakshadweep": [
        "Kavaratti"
    ],
    "Puducherry": [
        "Puducherry", "Karaikal", "Mahe", "Yanam"
    ]
}


def get_all_states():
    """Get list of all Indian states"""
    return sorted(INDIAN_STATES_CITIES.keys())


def get_cities_for_state(state):
    """Get cities for a given state"""
    return INDIAN_STATES_CITIES.get(state, [])


def validate_location(state, city):
    """Validate if city exists in the given state"""
    if state not in INDIAN_STATES_CITIES:
        return False
    return city in INDIAN_STATES_CITIES[state]
