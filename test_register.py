from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyodbc
import time
import uuid
import bcrypt

def save_full_report_to_db(email, name, password):
    print(f"DB: {email} icin SQL kayit islemi basliyor")
    try:
        conn = pyodbc.connect("DRIVER={SQL Server};SERVER=.;DATABASE=Login_idefix;Trusted_Connection=yes;")
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        
        if not row:
            cursor.execute("""
                INSERT INTO users (email, name, password, created_at) 
                OUTPUT INSERTED.id 
                VALUES (?, ?, ?, GETDATE())
            """, (email, name, password))
            user_id = cursor.fetchone()[0]
            print(f"USERS: Yeni kullanici eklendi ID: {user_id}")
        else:
            user_id = row[0]
            print(f"USERS: Kullanici DB'de mevcut ID: {user_id}")

        cursor.execute("""
            INSERT INTO login_logs (user_id, status, created_at) 
            VALUES (?, 'success', GETDATE())
        """, (user_id,))
        print("LOGIN_LOGS: Basarili giris logu eklendi")

        fake_token = f"idefix-test-{str(uuid.uuid4())[:13]}"
        cursor.execute("""
            INSERT INTO sessions (user_id, session_token, created_at) 
            VALUES (?, ?, GETDATE())
        """, (user_id, fake_token))
        print(f"SESSIONS: Oturum acildi Token: {fake_token}")

        conn.commit() 
        conn.close()
        print("BINGO: Tum tablolar guncellendi")
    except Exception as e:
        print(f"SQL Hatasi: {e}")

def dismiss_popup_if_present(driver, timeout=10):
    print("UI: Pop-up kontrolu yapiliyor")
    try:
        wait = WebDriverWait(driver, timeout)
        btn = wait.until(EC.element_to_be_clickable((By.XPATH,  "//*[@id='dengage_push-refuse-button']")))
        try:
            btn.click()
        except:
            driver.execute_script("arguments[0].click();", btn)
        print("UI: Pop-up temizlendi")
        time.sleep(2)
    except:
        print("UI: Pop-up yok devam ediliyor")

def run_full_test():
    test_email = "name@gmail.com" 
    test_password = "name1234"
    test_name = "name Test"

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    
    wait = WebDriverWait(driver, 30)

    try:
        print("UI: Idefix aciliyor")
        driver.get("https://www.idefix.com")
        time.sleep(3)
        
        dismiss_popup_if_present(driver)

        print("UI: Giris Yap butonuna tiklaniyor")
        
        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Giriş yap']/ancestor::a")))
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_btn)
        time.sleep(2) 
        
        try:
            login_btn.click() 
        except:
            print("UI: JS Click ile zorlaniyor")
            driver.execute_script("arguments[0].click();", login_btn)

        print("UI: Mail yaziliyor")
        email_field = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@name='emailOrPhone']")))
        time.sleep(1)
        email_field.send_keys(test_email)
        
        devam_btn = driver.find_element(By.XPATH, "//button[@type='submit' and contains(., 'Devam')]")
        devam_btn.click()
        
        time.sleep(4)

        print("UI: Sifre yaziliyor")
        pass_field = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@name='password']")))
        pass_field.send_keys(test_password)
        
        print("UI: Final butonuna tiklaniyor")
        final_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(., 'Giriş')]")))
        
        try:
            final_btn.click()
        except:
            driver.execute_script("arguments[0].click();", final_btn)
        
        print("UI: UI Islemleri tamamlandi DB senkronizasyonu bekleniyor")
        time.sleep(6) 

        save_full_report_to_db(test_email, test_name, test_password)

    except Exception as e:
        print(f"HATA: {e}")
    finally:
        print("Bot kapatiliyor")
        driver.quit()

if __name__ == "__main__":
    run_full_test()