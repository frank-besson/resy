from selenium import webdriver

# https://testdriven.io/blog/concurrent-web-scraping-with-selenium-grid-and-docker-swarm/

# options = webdriver.FirefoxOptions()
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# https://testdriven.io/blog/concurrent-web-scraping-with-selenium-grid-and-docker-swarm/
def get_driver(
    options=options,
    host='http://localhost:4444/wd/hub'
):
    return webdriver.Remote(
        options=options, 
        # desired_capabilities=DesiredCapabilities.CHROME,
        command_executor = host
    )