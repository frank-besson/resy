from selenium import webdriver

# options = webdriver.FirefoxOptions()
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')


def get_browser(
    options: webdriver.ChromeOptions = options,
    host: str = 'http://localhost:4444/wd/hub'
):
    '''
    Description:
        create instance of selenium.webdriver on host machine with
        "amd" cpu architecture

    Parameters:
        options (webdriver.ChromeOptions): options for invocation of webdriver
        host (str): address of machine hosting selenium

    Returns:
        (selenium.webdriver): invocation to be used to process web requests
    '''

    return webdriver.Remote(
        options=options, 
        # desired_capabilities=DesiredCapabilities.CHROME,
        command_executor = host
    )
