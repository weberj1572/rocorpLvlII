
import os
from Browser import Browser
from RPA.HTTP import HTTP
from RPA.Archive import Archive
from Browser.utils.data_types import SelectAttribute
from RPA.Robocorp.Vault import Vault
from RPA.Tables import Tables
import time
from RPA.PDF import PDF
from RPA.Dialogs import Dialogs


'''
Documentation       
[] Orders robots from RobotSpareBin Industries Inc.
    Open the robot order website
        #${orders}=    Get orders
        #FOR    ${row}    IN    @{orders}
        #    Close the annoying modal
        #    Fill the form    ${row}
        #    Preview the robot
        #    Submit the order
        #    ${pdf}=    Store the receipt as a PDF file    ${row}[Order number]
        #    ${screenshot}=    Take a screenshot of the robot    ${row}[Order number]
        #    Embed the robot screenshot to the receipt PDF file    ${screenshot}    ${pdf}
        #    Go to order another robot
        # END
        # Create a ZIP file of the receipts
[] Saves the order HTML receipt as a PDF file.
[] Saves the screenshot of the ordered robot.
[] Embeds the screenshot of the robot to the PDF receipt.
[] Creates ZIP archive of the receipts and the images.
'''

browser = Browser(auto_closing_level=True)
pdf = PDF()
archive = Archive()
dialogs = Dialogs()
VAULT = Vault()

def open_order_website():
    secret = VAULT.get_secret("SpareBinIndustries")
    order_url = secret["order_url"]
    browser.open_browser(order_url)
    
def user_input():
    dialogs.add_heading("Please provide the URL for downloading orders.")
    dialogs.add_text_input(name="url",label="URL")
    result = dialogs.run_dialog()
    return result.url
    

def close_annoying_modal():
    btn_click = browser.click("//button[normalize-space()='OK']")
    alert_btns_exist = browser.get_element("//div[@class='alert-buttons']")
    if alert_btns_exist:
        btn_click


def new_order():
    time.sleep(1)
    browser.click("//button[@id='order-another']")
    close_annoying_modal()
    
def get_orders(orders_csv):
    http = HTTP()
    http.download(url=orders_csv, overwrite=True)
    tbl = Tables()
    orders = tbl.read_table_from_csv("orders.csv", columns=["Order number","Head","Body","Legs","Address"])
    return orders


    
def fill_form(orders):
    for order in orders: 
        preview_shown = False
        first_attempt = 1
    
        while not preview_shown:
            try:
                
                o_body = order['Body']
                browser.select_options_by("//select[@id='head']", SelectAttribute["value"], order["Head"])
                browser.click(f"//input[@id='id-body-{o_body}']")
                browser.scroll_to(vertical='bottom')
                browser.type_text("css=body > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > form:nth-child(2) > div:nth-child(3) > input:nth-child(3)", order["Legs"]) 
                browser.type_text("//input[@id='address']", order["Address"])
                browser.click("//button[@id='preview']")
                preview_filename = f"{os.getcwd()}/output/preview_"+ str(order["Order number"]) + ".png"
                browser.take_screenshot(filename=preview_filename, selector=("//div[@id='robot-preview-image']"))
                preview_shown = True
                order_complete = False
                second_attempt = 1
                while not order_complete:
                    
                    browser.click("//button[@id='order']")
                    order_complete = generate_pdf(order["Order number"], preview_filename)
                    if order_complete: 
                        new_order()
                    if second_attempt == 6:
                        break
                    else:
                        second_attempt += 1
                # browser.click("//button[@id='order-another']")
            
            except:
                continue
            
            finally:
                if (preview_shown == True and order_complete == True) or first_attempt == 3:
                    break
                else:
                    preview_shown = False
                    first_attempt += 1
    
def generate_pdf(order_number, preview_filename):
    try:
        pdf_filename = f"{os.getcwd()}/output/receipt_"+ order_number+".pdf"
        receipt_html = browser.get_property(
            selector="xpath=//div[@id='receipt']", property="outerHTML")
        pdf.html_to_pdf(receipt_html, pdf_filename)
        # add image
        pdf.add_watermark_image_to_pdf(image_path=preview_filename,
                                       source_path=pdf_filename,
                                       output_path=pdf_filename)
        order_complete = True
    except: 
        order_complete = False
    return order_complete

        

def create_zip_file():
    archive.archive_folder_with_zip(folder=f"{os.getcwd()}/output/", 
                            archive_name=f"{os.getcwd()}/output/pdf_receipts.zip",
                            include="*.pdf")

    
    
def main():
    try:
        open_order_website()
        u_in = user_input()
        get_csv_orders = get_orders(u_in)
        close_annoying_modal()
        fill_form(get_csv_orders)
        create_zip_file()
    
    finally:
        browser.playwright.close()


if __name__ == "__main__":
    main()