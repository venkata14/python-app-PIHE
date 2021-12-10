mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml

echo "\
[general]\n\
email = \"venkata.patchigolla@uconn.edu\"\n\
" > ~/.streamlit/credentials.toml 

echo "API_KEY = \"AIzaSyAPgf37h-eTSW5SiBG28gpiRnghfZOwAY4\"" > ~/.streamlit/secrets.toml