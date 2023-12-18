import chartmogul
import  requests
import time
import dbhelper as db
from datetime import datetime, timedelta, date
import country_converter as coco
cc = coco.CountryConverter()
from dateutil.relativedelta import relativedelta    
config = chartmogul.Config('CHART_ID')
chartmogul.Ping.ping(config).get()
#Gumroad API key
api_key = 'YOUR_KEY'

""" Replace all the variables below with necessary IDs"""

#Replace with Gumroad product ID
product_id = 'ID'

#Gumroad API endpoint
endpointSub = 'https://api.gumroad.com/v2/products/%s/subscribers'%(product_id)

#Chartmogul datasource ID
dsID = "ds_ID"
planMap = {"Standard yearly":"pl_PLAN_ID","Pro yearly":"pl_PLAN_ID"}


""" End of replacement """

def getPlanID(s):
    if 'variants' not in s:
        print("LIFEIME")
        return ""
    k = s['variants']['Tier'] + " " + s['subscription_duration']
    return planMap[k]
    # == "monthly":
def getStartData(s):
    d = datetime.strptime(s['created_at'], "%Y-%m-%dT%H:%M:%SZ")
    """freeTrial = onFreeTrial(s)
    if freeTrial:
        return d + relativedelta(days=+7)    
    """
    return d.isoformat()

def getEndData(s):
    d = datetime.strptime(s['created_at'], "%Y-%m-%dT%H:%M:%SZ")
    freeTrial = onFreeTrial(s)
    if freeTrial:
        return freeTrial
    if s['subscription_duration'] == "monthly":
        d = d + relativedelta(months=+1) + relativedelta(days=-1)
    else:
        d = d + relativedelta(years=+1)        
    return d.isoformat()
def getCurr(s):
    if s == "$":
        return "USD"
    elif s == "€":
        return "EUR"
    elif s == "£":
        return "GBP"
    return "USD"

def onFreeTrial(s):
    free_trial_ends_on = datetime.strptime(s['free_trial_ends_on'], '%b %d, %Y')
    
    date = datetime.fromisoformat(s['created_at'].replace("Z",""))
    if free_trial_ends_on > date:
        print("Free trial is still active.")
        return free_trial_ends_on
    else:
        print("Free trial has ended.")
        return False
            
def getGumSale(email):
    headers = {}
    endpointSale = 'https://api.gumroad.com/v2/sales/'
    params = {'access_token':api_key, 'email':email}
    recurrInv = False
    next_page_url = endpointSale
    allData = []
    ref =  ""
    country = ""
    state = ""
    prevUrl = None
    while next_page_url:
        print("CALL")
        
        response = requests.get(endpointSale, headers=headers, params=params, timeout=10)
        sales = response.json()
        next_page_url = sales.get('next_page_url')
        if next_page_url:
            
            next_page_url = "https://api.gumroad.com" + next_page_url
            endpointSale = next_page_url
            if next_page_url == prevUrl:
                print("Same url, BREAK*****************")
                break            

        print("next_page_url",next_page_url)
        #print(sales)
        print("Total active sales",len(sales['sales']))
        print(next_page_url, prevUrl)        
   
        if sales:
            for s in sales['sales']:
                if "lifetime" in s["product_name" ].lower():
                    print("Skip lifetime")
                    continue
                print("***",s['created_at'])
                #Time to cut it?
                if db.isInvoiceExists(s['id']):
                    #print("CUTTING SALES LOOP")
                    pass
                    #next_page_url = False
                    #break
                

                #l =  s['license_key']
                #print("Processing",s['email'])
                #c_code = coco.convert(s['country'],to='ISO2')
                if not ref:
                    ref = s['referrer']
                if not country and "country_iso2" in s:
                    country = s['country_iso2']
                if not state and "state" in s:
                    state = s['state']
                
                plan = getPlanID(s)
                if not plan:
                    print("Skipping")
                    continue
                price = s['price']
                #if not s['recurring_charge']:
                freeTrial = onFreeTrial(s)
                if freeTrial or not  s['recurring_charge']:
                    price = 0
                else:
                    price = s['price']
                
                print("SEL**")
                #Free trial or upgrade
                data = {
                    "external_id": s['id'],
                    "myID":s['id'],
                    "date":s["created_at"],
                    "currency":getCurr(s['currency_symbol']),
                    "customer_external_id":s['email'],
                    "data_source_uuid":dsID,
                    "line_items": [ 
                        {
                            "type": "subscription",
                            'subscription_external_id':s['email'],
                            "plan_uuid":plan,
                            "service_period_start":getStartData(s),
                            "amount_in_cents":price,
                            "service_period_end":getEndData(s)
                        }
                    ]
                ,
                    "transactions": [{
                        "date": s['created_at'],
                        "type": "payment",
                        "result": "successful",
                        
                    }]
                }
                    
                
                    #print("Skipping free trial")
                    #data['transactions'] = []                
                allData.append(data)
            #Load url
            prevUrl = next_page_url

            
            """ '$email': s['email'],
                '$first_name': fName,
                'price':round(s['price']/100),
                'planType':s['subscription_duration'],
                'country':s['country'],
                'currency_symbol':s['currency_symbol'],
                '$country_code':c_code,
                '$city':None,
                'free_trial_ended':s['free_trial_ended'],
                'cancelled':s['cancelled']"""
            
        
    return [allData,ref,country, state]
            
allEmails = {}
def get2daysBack():
    s = datetime.now() + relativedelta(days=-10)
    return s.strftime("%Y-%m-%d")

def getAllSales(email = ""):
    fErr = open("error.txt", "w")
    f2 = open("log.txt", "w")
    headers = {}
    start = False
    print("Get all sales")
    endpointSale = 'https://api.gumroad.com/v2/sales/'
    params = {'access_token':api_key, 'product_id':product_id}

    #, 'after':get2daysBack()
    #}'after':get2daysBack()
    print(params)
    #quit()
    if email:
        params['email'] = email
    else:
        params['after'] = get2daysBack()
        pass

    next_page_url = endpointSale
    oldNextUrl = next_page_url
    oldID = ""
    page = 1
    next_page_key = None
    while next_page_url:
        print("WHILE LOOP")
        if next_page_key:
            params['page_key'] = next_page_key
        response = requests.get(endpointSale, headers=headers, params=params, timeout=10)
        sales = response.json()
        #print(sales)
        page += 1
        if not sales or 'sales' not in sales:
            print("NOPthing")
            print(sales)
            break
        if len(sales['sales']) == 0:
            break
        print("Done while", next_page_url)
        #print(sales)
        next_page_key = sales.get('next_page_key')
        if next_page_key:
            #next_page_url = "https://api.gumroad.com" + next_page_url
            print("next_page_key", next_page_key)
        
        #continue
        #print("Total active sales",len(sales['sales']))
        allData = []
        ref =  ""
        country = ""
        state = ""
        if sales:
            time.sleep(1)
            for s in sales['sales']:
                custEmail = s['email']
                print("custEmail", custEmail)
                print(allEmails)
                if 'full_name' in s:
                    fName = s['full_name']
                else:
                    fName = s['email'].split('@')[0]
                #Get all other sales for this users if this is the first time
                if custEmail not in allEmails.keys():
                    allEmails[custEmail] = ""
                    print("IN check")
                    created = s['created_at'][:10]
                    cust = {"data_source_uuid" : dsID,
                                "external_id": s['email'],
                                    'name': fName,
                                    'email': s['email'],
                                    'lead_created_at':created,
                                    'free_trial_started_at':created
                                    #'country': ''
                                    #'fields': {'subscribedOn':created,'recurrence':s['recurrence'],'subStatus':s['status']},             
                                    #'created_at':c
                                    }
                    invoicesOrTransactions, ref, country, state = getGumSale(s['email'])
                    
                    cust['attributes'] = {}
                    cust['attributes']['custom'] =  [
                    
                        {"type": "String", "key": "Referrer", "value": ref}
                    ]
                    cust['country'] = country
                    cust['state'] = state
                    print("invoicesOrTransactions",invoicesOrTransactions)
                    invoicesOrTransactions =  sorted(invoicesOrTransactions, key=lambda x:  datetime.fromisoformat(x['date'].replace("Z","")))
                    try:
                        alreadyCust = db.isCustomerExist(s['email'])
                        if alreadyCust:
                            print("CUst exists", alreadyCust[0])
                            processInvoice(alreadyCust[0], invoicesOrTransactions,s, already=True)
                        else:
                            chartmogul.Customer.create(config, data=cust).then(lambda custRes: processInvoice(custRes.uuid, invoicesOrTransactions,s, already = False) ).get()
                        f2.write(s['email'] + ":" + str(len(invoicesOrTransactions)))
                        f2.flush() 
                    except chartmogul.errors.APIError as e:
                        print(str(e))
                        #Can we update the new sales atleast?
                        print("Error failing siltenly")    
                        fErr.write(s['email'] + ":" + str(e))    
                        fErr.flush()            
                        #getS(s)
                    print("Loop done")
        if not next_page_key:
            print("No more")
            break
    fErr.close()
    f2.close()
""" NOt used """

def processInvoice(uuid, invoicesOrTransactions, s, already=False):  
    if not already:  
        db.insert_record("users", [s['email'], uuid]) 
    print("PROCESS",uuid)
    print("Invoices", invoicesOrTransactions)
    finalInv = []
    #Fresh invoice
    for inv in invoicesOrTransactions:
        if "currency" in inv:
            print("IN INVOICE", inv['external_id'])
            if db.isInvoiceExists(inv['myID']):                
                print("INvoice exists")
                continue
            del inv["myID"]
            finalInv.append(inv)
    print("finalInv",finalInv)    
    if finalInv:
        #Beofore creqating invoice, cancel old ones to handle upgrade cases    
        pass  

        proxyFn(uuid, finalInv, s)      

        """chartmogul.Subscription.list_imported(
        config,
        uuid=uuid,
        per_page=100).then(
            lambda a:cancelSubscription(a,s, proxyFn, uuid, inv)
        ).get()"""
                #time.sleep(1)
       
    if s['cancelled']:
        chartmogul.Subscription.list_imported(
        config,
        uuid=uuid,
        per_page=100).then(
            lambda a:cancelSubscription(a,s)
        ).get()

def proxyFn(uuid,invoices, s):
    print("Proxy")
    res = chartmogul.Invoice.create(
                    config,
                    uuid=uuid,
                    data={
                        "invoices": invoices}
                ).then(lambda invRes: cancel(uuid, invRes.invoices, s, invoices)).get()


def insertTransaction(s, trans):
    invoiceData = []
    #for invoice in invoices:
    date = datetime.fromisoformat(trans['date'].replace("Z",""))
    invoiceData.append([s['email'],trans['external_id'], date])
    if invoiceData:
        db.insert_array("transactions", invoiceData)
    print("Done inserting transaction", trans['external_id'])


def cancel(uuid, invoicesRes, s, invoices):
    #print("Cancel called", a.subscriptions)
    #process invoices
    #invoiceData = invoices.map(lambda x:  [x['external_id'],s['email']])
    invoiceData = []
    print("Cancel check INV", invoicesRes)
    for inv in invoicesRes:
        
        date = datetime.strftime(inv.date,"YYYY-mm-dd HH:MM:SS")
        invoiceData.append([ inv.external_id, s['email'],inv.uuid, date])
    if invoiceData:
        db.insert_array("invoices", invoiceData)
    if s['cancelled']:
        chartmogul.Subscription.list_imported(
        config,
        uuid=uuid,
        per_page=100).then(
            lambda a:cancelSubscription(a,s)
        ).get()

def cancelSubscription(a,s, returnFn = None, uuid = None, inv = None):
    if a.subscriptions:
        print("AAA",a.subscriptions[0])
        print("DATE",s['created_at'])
        #d = getStartData(s['created_at'])
        #print("NEw ", d)
        for sub in a.subscriptions:
            chartmogul.Subscription.cancel(
                        config,
                        uuid=sub.uuid,
                        data={"cancelled_at": s['created_at']}
                            
                            ).then(lambda a: returnFn(uuid, inv, s) if returnFn\
                                else print("Canceled***")
                            ).get()    
    else:
        print("nothing to cancel?", s['email'])
        if returnFn:
            returnFn(uuid, inv, s)


def listSubs():
    chartmogul.Subscription.list_imported(
    config,
    uuid="cus_ID",
    per_page=2).then(lambda a:print(a)).get()


#getAllSales()    

def testTrans():
    t = {'external_id': '_ID==', 'date': '2022-12-30T15:05:12Z', 'type': 'payment', 'result': 'successful', 'amount_in_cents': 899}
    
    chartmogul.Transaction.create(config, uuid="inv_ID", data=t).then(lambda tran: print(tran)).get()
    
#getAllSales(email="oliver.q.ellingson@gmail.com")
getAllSales()
#print(getGumSale("runjun.dutta@geneva.msf.org"))
#print(db.isInvoiceExists("Y3-jJ9kn91zW5c1_umQ2Rg=="))
#print(getGumSale("broodislekker@gmail.com"))
#tom@blue-zoo.co.uk
#createInvoiceTest()