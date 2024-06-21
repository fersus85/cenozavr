import os
import re
import csv
import time
import logging

from random import choice

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    WebDriverException,
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
    SessionNotCreatedException,
    InvalidElementStateException,
    ElementNotInteractableException
)

import undetected_chromedriver as uc
from dotenv import load_dotenv

from agents import user_agents


load_dotenv()

PROXY_USER: str = os.getenv('PROXY_USER')
PROXY_PASSWORD: str = os.getenv('PROXY_PASS')
PROXY_HOST: str = os.getenv('PROXY_HOST')
PROXY_PORT: str = os.getenv('PROXY_PORT')
PROXY_DIR = 'proxy_' + PROXY_HOST
PATH = os.path.join(os.getcwd(), PROXY_DIR)

USER_AGENT = choice(user_agents)
URL_MAIN = 'https://www.okeydostavka.ru'
ADDRESS = 'Москва, Малая Бронная улица, 32'
CATEGORIES = ('Товары со скидками', 'Бытовая химия')


logger = logging.getLogger(name=__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler(
    f'logs/{__name__}.log', mode='w', encoding='utf-8'
    )
formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")

handler.setFormatter(formatter)
logger.addHandler(handler)


def handle_exceptions(func: callable) -> callable:
    """
    Декоратор для обработки исключений, возникающих при выполнении функции.

    :param func (callable): Функция, для которой необходимо обработать
                            исключения.
    :return callable: Обёрнутая функция с обработкой исключений.

    Описание:
        Этот декоратор пытается выполнить переданную функцию и ловит различные
        исключения, связанные с работой драйвера Selenium. При возникновении
        исключения, информация о нём логируется. Если возникает неожиданное
        исключение, оно повторно поднимается после логирования.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NoSuchElementException as e:
            logger.error(f'Element not found: {e}', exc_info=True)
        except TimeoutException as e:
            logger.error(f'Timeout occurred: {e}', exc_info=True)
        except StaleElementReferenceException as e:
            logger.error(f'Stale element reference: {e}', exc_info=True)
        except SessionNotCreatedException as e:
            logger.error(f'Session not created: {e}', exc_info=True)
        except InvalidElementStateException as e:
            logger.error(f'Invalid element state: {e}', exc_info=True)
        except WebDriverException as e:
            logger.error(f'Webdriver exception: {e}', exc_info=True)
        except TypeError as e:
            logger.error(f'Webdriver exception: {e}', exc_info=True)
        except AttributeError as e:
            logger.error(f'Webdriver exception: {e}', exc_info=True)
        except Exception as e:
            logger.error(f'An unexpected error occurred: {e}', exc_info=True)
            raise
    return wrapper


def go_next_page(driver: uc.Chrome) -> uc.Chrome:
    '''
    Функция для перехода на следующую страницу категории.

    :param driver: веб-драйвер для управления браузером.
    :return: веб-драйвер для управления браузером.

    Описание:
        эта функция пытается выполнить переход на следующую
        страницу каталога, при возникновении исключения,
        информация о нём логируется.
    '''
    next = driver.find_elements(By.CLASS_NAME, 'right_arrow')
    try:
        next[0].click()
        logger.debug('press next page')
    except ElementNotInteractableException:
        logger.debug('next page dosnt exist')
    finally:
        return driver


@handle_exceptions
def find_element(driver: uc.Chrome, method: str, loc: str) -> WebElement:
    '''
    Функция для поиска элемента с ожиданием его загрузки.

    :param driver: веб-драйвер для управления браузером.
    :param method: str метод поиска.
    :param loc: str локатор искомого элемента.
    :return: WebElement искомый элемент.
    '''
    wait = WebDriverWait(driver, timeout=10)
    match method:
        case 'xpath':
            return wait.until(EC.presence_of_element_located((By.XPATH, loc)))
        case 'class_name':
            return wait.until(EC.presence_of_element_located(
                (By.CLASS_NAME, loc)))
        case 'css_selector':
            return wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, loc)))
        case 'id':
            return wait.until(EC.presence_of_element_located((By.ID, loc)))
        case 'tag_name':
            return wait.until(EC.presence_of_element_located(
                (By.TAG_NAME, loc)))
        case 'delivery':
            return wait.until(EC.element_to_be_clickable(
                (By.ID, loc)))
        case _:
            raise AttributeError('invalid name for parametr')


@handle_exceptions
def create_webdriver(user_agent: str,
                     headless: bool = True,
                     proxy: bool = True) -> uc.Chrome:
    '''
    Функция создаёт веб-драйвер для управления браузером.
    :param user_agent: str заголовок для браузера.
    :param headless: bool режим управления графического отображения
    :param proxy: str режим proxy server
    :return: веб-драйвер для управления браузером.
    '''
    options = uc.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--disable-notifications")
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.geolocation": 2})
    options.add_argument(f'--user-agent={user_agent}')
    if proxy:
        options.add_argument('--load-extension=' + PATH)
    driver = uc.Chrome(headless=headless, options=options)
    return driver


@handle_exceptions
def click_element(driver: uc.Chrome, element: WebElement) -> None:
    '''
    Функция для клика с дополнительным наведением на элемент.

    :param driver: веб-драйвер для управления браузером.
    :param element: WebElement, предназначенный для клика.
    '''
    actions = ActionChains(driver)
    actions.move_to_element(element).click().perform()


@handle_exceptions
def close_driver(driver: uc.Chrome) -> None:
    '''
    Функция для закрытия веб-драйвера.

    :param driver: веб-драйвер для управления браузером.
    '''
    driver.close()
    driver.quit()


@handle_exceptions
def select_delivery_address(driver: uc.Chrome,
                            delivery_address: str) -> uc.Chrome:
    '''
    Функция вводит и сохраняет адрес доставки.

    :param driver: веб-драйвер для управления браузером.
    :param delivery_address: str адрес доставки.
    :return: веб-драйвер для управления браузером с выбранным адресом.
    '''
    wait = WebDriverWait(driver, timeout=15)
    driver.get(URL_MAIN)
    click_element(driver, find_element(
        driver, 'xpath', "//button[contains(text(),'Принять')]"))
    logger.debug('press ok cookie')

    delivery = wait.until(EC.element_to_be_clickable(
        (By.ID,
         "availableReceiptTimeslot")))
    ActionChains(driver).move_to_element(delivery).perform()
    time.sleep(10)
    delivery.click()
    logger.debug('press delivery button')

    address = find_element(driver, 'css_selector', '#addressSelectionQuery')
    driver.implicitly_wait(15)
    address.send_keys(delivery_address)
    logger.debug('insert address in form')
    driver.implicitly_wait(15)
    address.send_keys(Keys.ENTER)
    address.send_keys(Keys.ENTER)
    logger.debug('press enter')

    save = wait.until(EC.element_to_be_clickable(
        (By.ID, 'addressSelectionButton')))
    ActionChains(driver).move_to_element(save).perform()
    save.click()
    logger.debug('press save delivery address')
    time.sleep(10)
    return driver


@handle_exceptions
def parse_products(driver: uc.Chrome,
                   categories: list,
                   pages: int = 2) -> list:
    '''
    Функция собирает информацию о товарах, представленных на сайте.

    :param driver: веб-драйвер для управления браузером.
    :param categories: list категории товаров для парсинга.
    :param pages: int кол-во необходимых страниц.
    :return: list список товаров.
    '''
    products_main = []
    for cat in categories:
        driver.get(URL_MAIN)
        xpass_category = f"//div[contains(text(),'{cat}')]"
        click_element(driver, find_element(driver, 'xpath', xpass_category))
        logger.debug('find category')
        driver.implicitly_wait(15)
        for _ in range(pages):
            wait = WebDriverWait(driver, timeout=10)
            cards = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CLASS_NAME, 'product.ok-theme'))
                )
            logger.debug('find products cards')
            for prod in cards:
                lst = []
                a = prod.find_element(By.TAG_NAME, 'a')
                lst.append(a.text)
                lst.append(a.get_attribute('href'))
                img_url = prod.find_element(By.TAG_NAME, 'img')
                lst.append(URL_MAIN + img_url.get_attribute('data-src'))
                el = prod.find_element(By.TAG_NAME, 'script')
                js_code = driver.execute_script(
                    "return arguments[0].innerHTML;", el
                    )
                category_pattern = r'category: "([^"]+)"'
                try:
                    category_match = re.search(category_pattern, js_code)
                    lst.append(category_match.group(1))
                except AttributeError:
                    lst.append('no category')
                    logger.warning('category not found')
                div_price = prod.find_element(By.CLASS_NAME, 'product-price')
                prices = div_price.find_elements(By.TAG_NAME, 'span')
                full_price = prices[0].get_attribute('textContent')
                price = prices[1].get_attribute('textContent')
                lst.append(full_price.strip()[:-2])
                lst.append(price.strip()[:-2])
                products_main.append(lst)
                logger.info('products added to main list')
            driver = go_next_page(driver)
            time.sleep(5)
    logger.debug('add products in main list')
    close_driver(driver)
    logger.debug('close driver')
    return products_main


@handle_exceptions
def save_to_csv(products: list) -> None:
    '''
    Функция сохраняет информацию в csv файл.

    :param products: list список для записи.
    '''
    csv_file = 'products.csv'
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(
            ['Наименование', 'Url_товара', 'Url_изображения', 'Категория',
             'Полная цена', 'Цена соскидкой']
            )
        for row in products:
            writer.writerow(row)


# создайте webdriver с необходимыми настройками
browser = create_webdriver(user_agent=USER_AGENT)

# выберите адрес доставки
browser = select_delivery_address(browser, ADDRESS)

# соберите информацию
prods = parse_products(browser, CATEGORIES)

# сохраните информацию в csv файл
save_to_csv(prods)
