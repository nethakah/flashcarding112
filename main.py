from cmu_graphics import *
import math, copy, time, json, os

##### Backend #####
dataFile = "flashcard_data.json"

def getDataPath():
    scriptDir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(scriptDir, dataFile)

def saveData(app):
    data = {"decks": []}
    for deck in app.decks:
        deckData = {"name": deck.name, "color": deck.color, "cards": []}
        for card in deck.cards:
            cardData = {
                "front": card.front,
                "back": card.back,
                "isLearning": card.isLearning,
                "learningStep": card.learningStep,
                "easeFactor": card.easeFactor,
                "interval": card.interval,
                "lastReviewTime": card.lastReviewTime
            }
            deckData["cards"].append(cardData)
        data["decks"].append(deckData)
    
    with open(getDataPath(), 'w') as f:
        json.dump(data, f, indent=2)

def loadData(app):
    dataPath = getDataPath()
    if not os.path.exists(dataPath):
        return
    
    with open(dataPath, 'r') as f:
        data = json.load(f)
    
    for deckData in data.get("decks", []):
        deck = Deck(deckData["name"], deckData.get("color", "lightBlue"))
        for cardData in deckData.get("cards", []):
            card = Flashcard(cardData["front"], cardData["back"])
            card.isLearning = cardData.get("isLearning", True)
            card.learningStep = cardData.get("learningStep", 0)
            card.easeFactor = cardData.get("easeFactor", 2.5)
            card.interval = cardData.get("interval", 0)
            card.lastReviewTime = cardData.get("lastReviewTime", None)
            deck.addCard(card)
        app.decks.append(deck)


##### Classes #####

class Flashcard:
    def __init__(self, front, back):
        self.front = front
        self.back = back
        
        # Learning phase variables
        self.isLearning = True
        self.learningStep = 0
            # step 0 = 1min
            # step 1 = 10min
            # step 2 = 1day
        
        # Review phase variables
        self.easeFactor = 2.5 # new interval = old interval * factor
        self.interval = 0
        self.lastReviewTime = None
    
    ### SPACED REPITITION ALGORITHM HERE ###
    def updateCard(self, rating):
        # new card logic
        if self.isLearning:
            
            # again
            if rating == 1:
                self.learningStep = 0 # reset learning step
                self.interval = 1
                
            # hard
            elif rating == 2:
                if self.learningStep == 0: 
                    # do not increment step on hard card unless its at step 0
                    self.interval = 6
                    self.learningStep = 1
                else:
                    self.interval = 10
                    # do not increment step
            
            # good
            elif rating == 3:
                self.learningStep += 1 # increment step if good
                
                if self.learningStep < 2:
                    self.interval = 10 # always 10mins on step1
                else: # step 2 or higher; done learning -> review
                    self.isLearning = False
                    self.interval = 1 * 24 * 60
            
            # easy
            elif rating == 4:
                # move to review immediately
                self.isLearning = False
                self.interval = 4 * 24 * 60
            
        
        # review card logic 
        else:
            # do not decrease ease below 130% (Anki faq)
            
            # again
            if rating == 1:
                self.easeFactor = max(1.3, self.easeFactor - 0.2) # drop easeFactor
                
                # relearn
                self.isLearning = True
                self.learningStep = 0
                self.interval = 1
            
            # hard (remembered but difficult)
            elif rating == 2:
                self.easeFactor = max(1.3, self.easeFactor - 0.15) # drop easeFactor
                self.interval *= 1.2 # increase interval but barely
            
            # good
            elif rating == 3:
                # easefactor unchanged
                self.interval *= self.easeFactor
                # normal exponential growth if remembered well
            
            # easy
            elif rating == 4:
                self.easeFactor = min(self.easeFactor + 0.15, 4) # capped at 4x
                self.interval *= self.easeFactor * 1.3 # +30% easy bonus v.s. Good
        
        # time
        self.lastReviewTime = time.time()
        self.interval = round(self.interval, 1)
    
    def isDue(self): # checks if you need to review this card
        if self.lastReviewTime == None:
            return True
        else:
            mins = (time.time() - self.lastReviewTime) / 60
            if mins >= self.interval: return True
            else: return False

class Deck:
    def __init__(self, name, color='lightBlue'):
        self.cards = []
        self.name = name
        self.color = color
    
    def emptyDeck(self):
        self.cards = []
    
    def addCard(self, card):
        self.cards.append(card)
    
    def delCard(self, card):
        if card in self.cards:
            self.cards.remove(card)
    
    def editCard(self, card, newFront=None, newBack=None):
        if card in self.cards:
            card.front = newFront
            card.back = newBack
    
    def getDueCards(self):
        result = []
        for card in self.cards:
            if card.isDue() and card.lastReviewTime != None and not card.isLearning:
                result.append(card)
        return result
    
    def getNewCards(self):
        result = []
        for card in self.cards:
            if card.lastReviewTime == None:
                result.append(card)
        return result
        
    def getLearningCards(self):
        result = []
        for card in self.cards:
            if card.isLearning and card.lastReviewTime != None:
                result.append(card)
        return result
    
    def getReviewCards(self):
        result = []
        for card in self.cards:
            if not card.isLearning:
                result.append(card)
        return result
    
    def getStats(self):
        total = len(self.cards)
        
        due = len(self.getDueCards())
        review = len(self.getReviewCards())
        learning = len(self.getLearningCards())
        new = len(self.getNewCards())
        
        return { 'Total': total,
                 'Due': due,
                 'Learn': learning,
                 'New': new, 
                 'Review': review }
 
class Button:
    def __init__(self, x, y, w, h, text, color='gray', textColor='white'):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = text
        self.color = color
        self.textColor = textColor
        self.isHoveringButton = False
    
    def drawButton(self):
        border = 'black' if self.isHoveringButton else self.color
        drawRect(self.x, self.y, self.w, self.h, 
                 fill=self.color, border=border)
        drawLabel(self.text, self.x + self.w/2, self.y + self.h/2,
                  size=16, fill=self.textColor, bold=True)
    
    def isMouseOnButton(self, mouseX, mouseY):
        return ((self.x <= mouseX <= self.x+self.w) and
                (self.y <= mouseY <= self.y+self.h))
    
    def updateHoveringState(self, mouseX, mouseY): # update hovering/highlighted button when we move mouse
        self.isHoveringButton = self.isMouseOnButton(mouseX, mouseY)


#### app ####
    
def onAppStart(app):
    app.width = 550
    app.height = 600
    app.decks = []
    app.currScreen = 'menu'
    
    # deck View
    app.currDeck = None
    
    # study View
    app.currCard = None
    app.showAnswer = False
    app.cardsDue = []
    
    # editCard View
    app.editingCard = None
    app.selectedInput = 'front'
    app.frontInput = ''
    app.backInput = ''
    
    # createDeck View
    app.deckNameInput = ''

    # menu buttons
    app.menuButtons = {
                       'decks': Button(app.width/2-80, 0, 80, 30, 'Decks', rgb(55,55,55)),
                       'add': Button(app.width/2, 0, 80, 30, 'Add', rgb(55,55,55)),
                       'createDeck': Button(app.width/2-55, app.height-30, 110, 30, 'Create Deck', rgb(55,55,55))
                        }
    
    # createDeck buttons
    w, h = 400, 125
    x, y = app.width/2-w/2, app.height/2-h/2
    buttonY = y + h - 40
    buttonW, buttonH = 75, 20
    app.createDeckButtons = { 
                             'cancel': Button(x+w-180, buttonY, buttonW, buttonH, 'Cancel', rgb(100,100,100)),
                             'ok': Button(x+w-100, buttonY, buttonW, buttonH, 'OK', rgb(120,120,120))
                              }
   
    # study buttons
    buttonY = app.height-80
    buttonW = 75
    buttonH = 20
    app.studyButtons = { 
                        'deleteDeck': Button(0, 0, 110, 30, 'Delete Deck', rgb(100,100,100)),
                        'edit': Button(app.width-100, 0, 100, 30, 'Edit Card', rgb(100,100,100)),
                        'showAnswer': Button(app.width/2-60, app.height-50, 120, 30, 'Show Answer', rgb(100,100,100)),
                        'again': Button(app.width/2-180, buttonY, buttonW, buttonH, 'Again', rgb(100,100,100)),
                        'hard': Button(app.width/2-85, buttonY, buttonW, buttonH, 'Hard', rgb(100,100,100)),
                        'good': Button(app.width/2+10, buttonY, buttonW, buttonH, 'Good', rgb(100,100,100)),
                        'easy': Button(app.width/2+105, buttonY, buttonW, buttonH, 'Easy', rgb(100,100,100))
                         }
    
    # editCard buttons
    app.editCardButtons = {
                           'delete': Button(app.width-110, 0, 110, 30, 'Delete Card', rgb(100,100,100)),
                           'close': Button(app.width/2-85, buttonY, buttonW, buttonH, 'Close', rgb(100,100,100)),
                           'add': Button(app.width/2+10, buttonY, buttonW, buttonH, 'Add', rgb(120,120,120))
                            }

    # load user's config of decks/cards
    loadData(app)

### draw App ###

def redrawAll(app):
    drawRect(0, 0, app.width, app.height, fill=rgb(86, 86, 86)) # background
    
    if app.currScreen == 'menu':
        drawMenuScreen(app)
    elif app.currScreen == 'study':
        drawStudyScreen(app)
    elif app.currScreen == 'editCard':
        drawEditCardScreen(app)
    elif app.currScreen == 'createDeck':
        drawNewDeckScreen(app)

def drawNavButtons(app):
    topNavButtons = ['decks', 'add']
    for button in topNavButtons:
        app.menuButtons[button].drawButton()

def drawMenuScreen(app):
    drawNavButtons(app)
    app.menuButtons['createDeck'].drawButton()
    
    # decks
    boxTop = 60
    boxLeft = 20
    boxWidth = app.width - 2*boxLeft
    boxHeight = app.height-100
    
    # header
    drawRect(boxLeft, boxTop, boxWidth, boxHeight, fill=rgb(60, 60, 60))
    drawLabel('Deck', boxLeft+40, boxTop+30, size=16, fill='white', bold=True)
    drawLabel('Due', boxLeft+boxWidth-40, boxTop+30, size=16, fill='white', bold=True)
    drawLabel('Learn', boxLeft+boxWidth-110, boxTop+30, size=16, fill='white', bold=True)
    drawLabel('New', boxLeft+boxWidth-180, boxTop+30, size=16, fill='white', bold=True)
    drawLine(boxLeft+20, boxTop+50, boxLeft+boxWidth-20, boxTop+50, lineWidth=1)
    
    # decks list
    headerHeight = 50
    startTop = boxTop + headerHeight + 35
    rowHeight = 30
    
    # draw deck rows
    for i in range(len(app.decks)):
        deck = app.decks[i]
        rowTop = startTop + i*rowHeight
        
        # add only if the screen is not full
        if (rowTop+rowHeight >= boxTop+headerHeight and 
            rowTop+rowHeight <= boxTop+boxHeight):
            drawMenuScreenDeckRow(app, deck, rowTop, i, boxLeft, boxWidth)
    
def drawMenuScreenDeckRow(app, deck, y, index, boxLeft, boxWidth):
    stats = deck.getStats()
    
    drawCircle(boxLeft+25, y+15, 6, fill=deck.color)
    drawRect(boxLeft, y, boxWidth, 30, fill=None, border=None)
    drawLabel(deck.name, boxLeft+40, y+15, size=14, fill='white', align='left')
    
    # new cards
    if stats['New'] > 0:
        newColor = rgb(0, 183, 235) #blue
    else:
        newColor = rgb(100, 100, 100)
    drawLabel(str(stats['New']), boxLeft+boxWidth-180, y+15, size=14, fill=newColor, bold=True)
    
    # learning cards
    if stats['Learn'] > 0:
        learnColor = rgb(255, 0, 0) #red
    else:
        learnColor = rgb(100, 100, 100)
    drawLabel(str(stats['Learn']), boxLeft+boxWidth-110, y+15, size=14, fill=learnColor, bold=True)
    
    # due cards
    if stats['Due'] > 0:
        dueColor = rgb(102, 255, 0) #green
    else:
        dueColor = rgb(100,100,100)
    drawLabel(str(stats['Due']), boxLeft+boxWidth-40, y+15, size=14, fill=dueColor, bold=True)

def drawNewDeckScreen(app):
    drawMenuScreen(app)
    drawRect(0, 0, app.width, app.height, fill=rgb(40,40,40), opacity=70)
    
    # dialog attributes
    w = 400
    h = 125
    x = app.width/2 - w/2
    y = app.height/2 - h/2
    drawRect(x, y, w, h, fill=rgb(70,70,70), border=rgb(100,100,100), borderWidth=2)
    
    drawLabel('New deck name:', x+20, y+30, size=14, fill='white', align='left')
    
    inputX = x+20
    inputY = y+45
    inputW = w-40
    inputH = 25
    
    drawRect(inputX, inputY, inputW, inputH, fill=rgb(90,90,90),
             border=rgb(100,100,100), borderWidth=3)
    
    drawLabel(app.deckNameInput, inputX+10, inputY+inputH/2, size=16,
              fill='white', align='left')
    
    for button in app.createDeckButtons.values():
        button.drawButton()
    
def drawStudyScreen(app):
    drawNavButtons(app)
    
    # done with deck
    if len(app.cardsDue) == 0 or app.currCard == None:
        drawLabel("Yay! You're all done with this deck for now.", 
                  app.width/2, app.height/2, size=24, fill='pink', bold=True)
        return
    
    card = app.currCard
    drawLabel(card.front, app.width/2, 150, size=24, fill='white')
    
    if not app.showAnswer:
        stats = app.currDeck.getStats()
        statsY = app.height-70
        
        # draw stats & answer button & delete deck button
        drawLabel(str(stats['New']), app.width/2-30, statsY,
                  fill=rgb(0, 183, 235), size=16, bold=True)
        drawLabel(str(stats['Learn']), app.width/2, statsY,
                  fill=rgb(255, 0, 0), size=16, bold=True)
        drawLabel(str(stats['Due']), app.width/2+30, statsY,
                  fill=rgb(102, 255, 0), size=16, bold=True)
        app.studyButtons['showAnswer'].drawButton()
        app.studyButtons['deleteDeck'].drawButton()
        
    else: # already revealed answer
        
        #divider line
        drawLine(50, 200, app.width-50, 200, fill='gray', lineWidth=3)
        
        #back
        drawLabel(card.back, app.width/2, 280, size=24, fill='white')
        
        #show the next interval when selecting rating
        intervals = previewIntervalsIfRated(card)
        buttonY = app.height-80
        buttonW = 75
        drawLabel(intervals['again'], app.width/2-180+buttonW/2,  buttonY-15, size=14, fill='red')
        drawLabel(intervals['hard'], app.width/2-85+buttonW/2,  buttonY-15, size=14, fill='orange')
        drawLabel(intervals['good'], app.width/2+10+buttonW/2,  buttonY-15, size=14, fill='lightGreen')
        drawLabel(intervals['easy'], app.width/2+105+buttonW/2,  buttonY-15, size=14, fill='lightGreen')
        
        # 'edit': Button(app.width-100, 0, 100, 30, 'Edit Card', rgb(100,100,100)),
        # 'showAnswer': Button(app.width/2-60, app.height-50, 120, 30, 'Show Answer', rgb(100,100,100)),
        # 'again': Button(app.width/2-180, buttonY, buttonW, buttonH, 'Again', rgb(100,100,100)),
        # 'hard': Button(app.width/2-85, buttonY, buttonW, buttonH, 'Hard', rgb(100,100,100)),
        # 'good': Button(app.width/2+10, buttonY, buttonW, buttonH, 'Good', rgb(100,100,100)),
        # 'easy': Button(app.width/2+105, buttonY, buttonW, buttonH, 'Easy', rgb(100,100,100))
        
        #rating currCard
        buttons = ['edit', 'again', 'hard', 'good', 'easy']
        for button in buttons:
            app.studyButtons[button].drawButton()

def drawEditCardScreen(app):
    drawNavButtons(app)
    
    for button in app.editCardButtons.values():
        button.drawButton()
    
    # front input box
    drawLabel('> Front', 50, 100, size=16, fill='white', align='left')
    frontFill = 'lightGray' if app.selectedInput == 'front' else 'gray'
    drawRect(50, 110, 450, 30, fill=frontFill)
    drawLabel(app.frontInput, 60, 125, size=16, fill='white', align='left')
    
    # back input box
    drawLabel('> Back', 50, 170, size=16, fill='white', align='left')
    backFill = 'lightGray' if app.selectedInput == 'back' else 'gray'
    drawRect(50, 180, 450, 30, fill=backFill)
    drawLabel(app.backInput, 60, 195, size=16, fill='white', align='left')

### Mouse events ###

def onMousePress(app, mouseX, mouseY):
    handleNavClick(app, mouseX, mouseY)
    
    if app.currScreen == 'menu':
        handleMenuClick(app, mouseX, mouseY)
    elif app.currScreen == 'study':
        handleStudyClick(app, mouseX, mouseY)
    elif app.currScreen == 'editCard':
        handleEditCardClick(app, mouseX, mouseY)
    elif app.currScreen == 'createDeck':
        handleCreateDeckClick(app, mouseX, mouseY)

def onMouseMove(app, mouseX, mouseY):
    topMenuButtons = ['decks', 'add']
    for button in topMenuButtons:
        app.menuButtons[button].updateHoveringState(mouseX, mouseY) # always update nav bar
    
    # re-check and highlight whatever button we are hovering over depending on menu (what buttons exist on screen)
    if app.currScreen == 'menu':
        for button in app.menuButtons.values():
            button.updateHoveringState(mouseX, mouseY)
    elif app.currScreen == 'createDeck':
        for button in app.createDeckButtons.values():
            button.updateHoveringState(mouseX, mouseY)
    elif app.currScreen == 'study':
        for button in app.studyButtons.values():
            button.updateHoveringState(mouseX, mouseY)
    elif app.currScreen == 'editCard':
        for button in app.editCardButtons.values():
            button.updateHoveringState(mouseX, mouseY)

def handleNavClick(app, mouseX, mouseY):
    if app.menuButtons['decks'].isMouseOnButton(mouseX, mouseY):
        app.currScreen = 'menu'
        app.currDeck = None
    elif (app.menuButtons['add'].isMouseOnButton(mouseX, mouseY) and app.currDeck != None):
        app.currScreen = 'editCard'
        app.editingCard = None
        app.frontInput = ''
        app.backInput = ''
        app.selectedInput = 'front'

def handleMenuClick(app, mouseX, mouseY):
    # need to update these values in TWO locations; maybe add class later
    boxTop = 60
    boxLeft = 20
    boxWidth = app.width - 2*boxLeft
    boxHeight = app.height-100
    headerHeight = 50
    startTop = boxTop + headerHeight + 35
    rowHeight = 30
    
    for i in range(len(app.decks)):
        deck = app.decks[i]
        rowTop = startTop + i*rowHeight
        
        # check if clicking this deckRow
        if (boxLeft <= mouseX <= boxLeft+boxWidth and
            boxTop+headerHeight <= rowTop <= boxTop+boxHeight and
            rowTop <= mouseY <= rowTop+rowHeight):
                
            app.currScreen = 'study'
            app.currDeck = deck
            
            # set all due cards to keep track of
            allCards = []
            allCards.extend(deck.getDueCards())
            allCards.extend(deck.getLearningCards())
            allCards.extend(deck.getNewCards())
            app.cardsDue = allCards
            
            if len(app.cardsDue) > 0:
                app.currCard = app.cardsDue[0]
                app.showAnswer = False
            else: # empty deck
                app.currCard = None
                print(f"No cards due for {deck.name}")
    
    if app.menuButtons['createDeck'].isMouseOnButton(mouseX, mouseY):
        app.currScreen = 'createDeck'
        app.deckNameInput = ''
        app.selectedInput = 'deckName'

def handleCreateDeckClick(app, mouseX, mouseY):
    w = 400
    h = 125
    x = app.width/2-w/2
    y = app.height/2-h/2
    
    inputX = x+20
    inputY = y+45
    inputW = w-40
    inputH = 25
    
    # click to type name
    if (inputX <= mouseX <= inputX+inputW and
        inputY <= mouseY <= inputY+inputH):
        app.selectedInput = 'deckName'

    # ok
    elif app.createDeckButtons['ok'].isMouseOnButton(mouseX, mouseY):
        if app.deckNameInput.strip() != '': # check not empty name
            newDeck = Deck(app.deckNameInput.strip())
            app.decks.append(newDeck)
            app.currScreen = 'menu'
    
    # cancel
    elif app.createDeckButtons['cancel'].isMouseOnButton(mouseX, mouseY):
        app.currScreen = 'menu'
    
    saveData(app)

def handleStudyClick(app, mouseX, mouseY):
    if app.cardsDue == []:
        return
    
    # delete this deck
    if app.studyButtons['deleteDeck'].isMouseOnButton(mouseX, mouseY):
        app.decks.remove(app.currDeck)
        app.currDeck=None
        app.currCard=None
        app.cardsDue = []
        app.currScreen = 'menu'
    
    # answer button
    elif not app.showAnswer:
        if app.studyButtons['showAnswer'].isMouseOnButton(mouseX, mouseY):
            app.showAnswer = True
    
    # edit current card
    elif app.studyButtons['edit'].isMouseOnButton(mouseX, mouseY):
        app.currScreen = 'editCard'
        app.editingCard = app.currCard
        app.frontInput = app.currCard.front
        app.backInput = app.currCard.back
        app.selectedInput = 'front'
    
    # rating buttons
    elif app.studyButtons['again'].isMouseOnButton(mouseX, mouseY):
        rateCard(app, 1)
    elif app.studyButtons['hard'].isMouseOnButton(mouseX, mouseY):
        rateCard(app, 2)
    elif app.studyButtons['good'].isMouseOnButton(mouseX, mouseY):
        rateCard(app, 3)
    elif app.studyButtons['easy'].isMouseOnButton(mouseX, mouseY):
        rateCard(app, 4)
    
    saveData(app)

def handleEditCardClick(app, mouseX, mouseY):
    # frontside
    if 50 <= mouseX <= 500 and 110 <= mouseY <= 140:
        app.selectedInput = 'front'
    
    # backside
    elif 50 <= mouseX <= 500 and 180 <= mouseY <= 210:
        app.selectedInput = 'back'
    
    # close/cancel editing
    elif app.editCardButtons['close'].isMouseOnButton(mouseX, mouseY):
        if app.cardsDue == []:
            app.currScreen = 'menu'
        else:
            app.currScreen = 'study'
            #also update the currCard if we just added a new card to empty deck
            if app.currCard==None and len(app.cardsDue)>0:
                app.currCard = app.cardsDue[0]
                app.showAnswer=False
    
    # save new edits
    elif app.editCardButtons['add'].isMouseOnButton(mouseX, mouseY):
        # make sure smth is entered
        if app.frontInput.strip() != '' and app.backInput.strip() != '':
            if app.editingCard != None:
                # edit this card
                app.editingCard.front = app.frontInput.strip()
                app.editingCard.back = app.backInput.strip()
            elif app.editingCard == None:
                # create new card
                newCard = Flashcard(app.frontInput.strip(), app.backInput.strip())
                app.currDeck.addCard(newCard)
                app.cardsDue.append(newCard)
            
            # reset everything
            app.frontInput = ''
            app.backInput = ''
            app.editingCard = None
            app.selectedInput = 'front'
    
    # delete current card
    elif app.editCardButtons['delete'].isMouseOnButton(mouseX, mouseY):
        if app.editingCard != None: # only if editing a card ('None' = creating a new card)
            app.currDeck.delCard(app.currCard)
            
            try:
                app.cardsDue.remove(app.currCard)
            except ValueError:
                pass
            
            if len(app.cardsDue) > 0:
                app.currScreen = 'study'
                app.currCard = app.cardsDue[0]
                app.showAnswer = False
            else:
                app.currScreen = 'study'
                app.currCard = None
        
        app.editingCard = None
    
    saveData(app)

### Key-press events ###

def onKeyPress(app, key):
    if app.currScreen == 'menu':
        handleMenuKeyPress(app, key)
    elif app.currScreen == 'study':
        handleStudyKeyPress(app, key)
    elif app.currScreen == 'editCard':
        handleEditCardKeyPress(app, key)
    elif app.currScreen == 'createDeck':
        handleCreateDeckKeyPress(app, key)

def handleMenuKeyPress(app, key):
    if key == 's':
        createSampleDeck(app)
    elif key == 't':
        skipTime(app, 24)

def handleCreateDeckKeyPress(app, key):
    if app.selectedInput == 'deckName':
        if key == 'backspace':
            app.deckNameInput = app.deckNameInput[:-1]
        elif key == 'enter': # create new deck
            if app.deckNameInput.strip() != '': # not empty name
                newDeck = Deck(app.deckNameInput.strip())
                app.decks.append(newDeck)
                app.currScreen = 'menu'
        elif key == 'space':
            app.deckNameInput += ' '
        elif len(key) == 1:
            app.deckNameInput += key
    
    saveData(app)

def handleStudyKeyPress(app, key):
    if app.cardsDue == []:
        return
    
    if key == 'space' and not app.showAnswer:
        app.showAnswer = not app.showAnswer
    elif app.showAnswer:
        if key == '1':
            rateCard(app, 1)
        elif key == '2':
            rateCard(app, 2)
        elif key == '3':
            rateCard(app, 3)
        elif key == '4':
            rateCard(app, 4)

def handleEditCardKeyPress(app, key):
    if app.selectedInput == 'front':
        if key == 'backspace':
            app.frontInput = app.frontInput[:-1]
        elif key == 'tab' or key == 'enter':
            app.selectedInput = 'back'
        elif key == 'space':
            app.frontInput += ' '
        elif len(key) == 1: # type char
            app.frontInput += key
    
    elif app.selectedInput == 'back':
        if key == 'backspace':
            app.backInput = app.backInput[:-1]
        elif key == 'tab':
            app.selectedInput = 'front'
        elif key == 'space':
            app.backInput += ' '
        elif len(key) == 1:
            app.backInput += key
        elif key == 'enter':
            # reused code from mouse click
            if app.frontInput.strip() != '' and app.backInput.strip() != '':
                if app.editingCard != None:
                    app.editingCard.front = app.frontInput.strip()
                    app.editingCard.back = app.backInput.strip()
                elif app.editingCard == None:
                    newCard = Flashcard(app.frontInput.strip(), app.backInput.strip())
                    app.currDeck.addCard(newCard)
                    app.cardsDue.append(newCard)
                    
                app.frontInput = ''
                app.backInput = ''
                app.editingCard = None
                app.selectedInput = 'front'
    
    saveData(app)

### Refiling helpers ###

def rateCard(app, rating):
    app.currCard.updateCard(rating)
    app.cardsDue.remove(app.currCard) #rated
    
    # check if short interval and re-add to end if its short instead of leaving removed
    if app.currCard.isLearning and app.currCard.interval <= 10:
        app.cardsDue.append(app.currCard)

    # refresh queue (move onto next card)    
    if len(app.cardsDue) > 0:
        app.currCard = app.cardsDue[0]
        app.showAnswer = False
    else: # we are DONE!
        app.currCard = None
    
    saveData(app)

def previewIntervalsIfRated(card):
    intervals = {'again': '<1m'}
    
    if card.isLearning == True:
        intervals['hard'] = '<6m' if card.learningStep == 0 else '<10m'
        intervals['good'] = '<10m' if card.learningStep == 0 else '1d'
        intervals['easy'] = '4d'
    else:
        currInterval = card.interval
        
        hardInterval = currInterval * 1.2
        intervals['hard'] = makeNiceLooking(hardInterval)
        
        goodInterval = currInterval * card.easeFactor
        intervals['good'] = makeNiceLooking(goodInterval)
        
        easyInterval = currInterval * (card.easeFactor * 1.3)
        intervals['easy'] = makeNiceLooking(easyInterval)
        
    return intervals

def makeNiceLooking(mins):
    if mins < 60:
        return f'{int(mins)}m'
    elif mins < 60*24:
        hrs = mins//60
        return f'{hrs}h'
    else:
        days = mins // (24*60)
        return f'{days}d'

### Grading Helpers ###

def skipTime(app, hrs):
    for deck in app.decks:
        for card in deck.cards:
            if card.lastReviewTime != None:
                card.lastReviewTime -= hrs*60*60 # conv to seconds
    
    saveData(app)

def createSampleDeck(app):
    sample = Deck('Example: Python Basics', 'purple')
    sample.addCard(Flashcard('What word defines a function?', 'def'))
    sample.addCard(Flashcard('What does len(L) return?', 'length of L'))
    sample.addCard(Flashcard('Types of loops', 'for and while'))
    sample.addCard(Flashcard('Can all recursive functions be rewritten iteratively?', 'Yes'))
    sample.addCard(Flashcard('What is the big-O runtime for len()?', 'O(1)'))
    sample.addCard(Flashcard('Immutable types', 'int, float, str, tuple'))
    sample.addCard(Flashcard('Mutable types', 'list, dict, set'))
    sample.addCard(Flashcard('+ vs += for lists', 'nonmutating vs mutating'))
    sample.addCard(Flashcard('How do sets search in O(1)?', 'using hashtables'))
    sample.addCard(Flashcard('What does __init__ do in a class?', 'sets base attributes'))
    app.decks.append(sample)
    saveData(app)

def main():
    runApp()

main()
