from selenium import webdriver

# options = webdriver.FirefoxOptions()
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')


def get_browser(
    options: webdriver.ChromeOptions = options
) -> webdriver:
    '''
    Description:
        create instance of selenium.webdriver on host machine with
        "arch" cpu architecture

    Parameters:
        options (webdriver.ChromeOptions): options for invocation of webdriver

    Returns:
        (selenium.webdriver): invocation to be used to process web requests
    '''

    return webdriver.Chrome(
        options=options, 
    )
        