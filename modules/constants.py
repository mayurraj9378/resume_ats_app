"""Static data used across the app."""

STOPWORDS = {
    "a", "about", "above", "after", "again", "all", "also", "am", "an", "and", "any", "are", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can", "could",
    "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further", "had", "has",
    "have", "having", "he", "her", "here", "him", "his", "how", "i", "if", "in", "into", "is", "it", "its",
    "just", "me", "more", "most", "my", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "our", "out", "over", "own", "same", "she", "should", "so", "some", "such", "than", "that", "the",
    "their", "them", "then", "there", "these", "they", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom",
    "why", "will", "with", "would", "you", "your", "etc", "using", "use", "work", "working", "team",
    "teams", "experience", "years", "year", "ability", "strong", "good", "great", "looking", "role",
    "required", "requirements", "responsibilities", "preferred", "must", "should", "job", "candidate",
    "company", "skills", "knowledge", "understanding", "including", "within", "across", "new",
}

SKILL_DB = [
    # languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "kotlin", "sql", "bash", "php", "ruby",
    # backend / frameworks
    "spring boot", "spring", "django", "flask", "fastapi", "node.js", "express", "react", "angular", "vue",
    "next.js", "hibernate", "rest api", "restful", "microservices", "graphql",
    # data / db
    "mysql", "postgresql", "mongodb", "redis", "oracle", "sqlite", "pandas", "numpy", "scikit-learn",
    "tensorflow", "pytorch", "machine learning", "data science", "data analysis", "power bi", "tableau",
    # devops / cloud
    "docker", "kubernetes", "aws", "azure", "gcp", "jenkins", "ci/cd", "git", "github", "gitlab", "linux",
    "terraform", "ansible", "nginx", "render", "netlify",
    # testing
    "selenium", "junit", "testng", "pytest", "postman", "cypress", "playwright", "rest assured", "jmeter",
    "test automation", "manual testing", "api testing", "regression testing", "test cases", "bug tracking",
    "jira", "sdet", "qa", "tdd", "bdd", "cucumber",
    # networking / security
    "tcp/ip", "dns", "http", "https", "ssl", "tls", "vpn", "firewall", "routing", "switching", "ccna",
    "jwt", "oauth", "authentication", "authorization", "cybersecurity",
    # general
    "agile", "scrum", "oop", "data structures", "algorithms", "design patterns", "html", "css", "json",
    "xml", "api", "debugging", "problem solving", "communication", "leadership",
]

ACTION_VERBS = {
    "achieved", "automated", "analyzed", "architected", "built", "collaborated", "created", "debugged",
    "decreased", "delivered", "deployed", "designed", "developed", "drove", "enhanced", "engineered",
    "established", "executed", "implemented", "improved", "increased", "integrated", "launched", "led",
    "maintained", "managed", "migrated", "optimized", "orchestrated", "reduced", "refactored", "resolved",
    "scaled", "secured", "streamlined", "tested", "trained", "validated", "wrote",
}

SECTION_PATTERNS = {
    "Summary / Objective": r"\b(summary|objective|profile|about me)\b",
    "Education": r"\beducation\b|\bacademic",
    "Experience": r"\b(experience|internship|employment|work history)\b",
    "Projects": r"\bprojects?\b",
    "Skills": r"\b(skills|technologies|technical skills|tech stack)\b",
    "Certifications": r"\b(certifications?|certificates?|courses)\b",
}

REQUIRED_SECTIONS = ["Education", "Experience", "Skills", "Projects"]
