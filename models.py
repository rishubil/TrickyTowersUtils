#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BaseModel:
    def __init__(self, pm, ptr):
        self.pm = pm
        self.ptr = ptr
        # print(f'{self.__class__.__name__}({hex(self.ptr)})')

    def print_tree(self, name=None, depth=0):
        tab = '  ' * depth
        name_str = f'{name}: ' if name else ''
        print(f'{tab}{name_str}{self.__class__.__name__}({hex(self.ptr)})')
        vs = vars(self)
        for attr_name in vs:
            if attr_name in ('pm', 'ptr'):
                continue
            attr = vs[attr_name]
            if isinstance(attr, BaseModel):
                attr.print_tree(attr_name, depth + 1)
            else:
                print(f'{tab}  {attr_name}: {attr}')


class DataModel(BaseModel):
    @property
    def value(self):
        raise NotImplementedError()

    def print_tree(self, name=None, depth=0):
        tab = '  ' * depth
        name_str = f'{name}: ' if name else ''
        # print(
        #     f'{tab}{name_str}{self.__class__.__name__}({hex(self.ptr)}) = {self.value}'
        # )
        print(f'{tab}{name_str}: {self.value}')


class Array(BaseModel):
    def __init__(self, pm, ptr, _type_init):
        super().__init__(pm, ptr)
        self._type_init = _type_init
        if ptr == 0x0:
            self._size = 0
            self._first_ptr = 0
            return
        self._size = pm.read_int(ptr + 0xc)
        self._first_ptr = ptr + 0x10

    def index_ptr(self, index):
        return self._first_ptr + 0x4 * index

    def get(self, index):
        return self._type_init(self.index_ptr(index))

    def print_tree(self, name=None, depth=0):
        tab = '  ' * depth
        name_str = f'{name}: ' if name else ''
        print(
            f'{tab}{name_str}{self.__class__.__name__}({hex(self.ptr)}) = size({self._size})'
        )
        for i in range(self._size):
            v = self.get(i)
            if isinstance(v, BaseModel):
                v.print_tree(f'index({i})', depth + 1)
            else:
                print(f'{tab}  index({i}): {v}({hex(self.index_ptr(i))})')


class GenericList(BaseModel):
    '''
    6782578 : System.Collections.Generic.List`1[T]
        static fields
            0 : EmptyArray (type: T[])
        fields
            8 : _items (type: T[])
            c : _size (type: System.Int32)
            10 : _version (type: System.Int32)
    '''

    def __init__(self, pm, ptr, _type_init):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self._items = None
            self._size = 0
            self._version = None
            return
        self._items = Array(pm, pm.read_int(ptr + 0x8), _type_init)
        self._size = pm.read_int(ptr + 0xc)
        self._version = pm.read_int(ptr + 0x10)

    def get(self, index):
        return self._items.get(index)


class GenericDictionary(DataModel):
    '''
        17000198 : System.Collections.Generic.Dictionary`2[TKey,TValue]
			static fields
				0 : <>f__am$cacheB (type: System.Collections.Generic.Dictionary.Transform<TKey,TValue,System.Collections.DictionaryEntry>)
			fields
				8 : table (type: System.Int32[])
				c : linkSlots (type: System.Collections.Generic.Link[])
				10 : keySlots (type: TKey[])
				14 : valueSlots (type: TValue[])
				18 : touchedSlots (type: System.Int32)
				1c : emptySlot (type: System.Int32)
				20 : count (type: System.Int32)
				24 : threshold (type: System.Int32)
				28 : hcp (type: System.Collections.Generic.IEqualityComparer<TKey>)
				2c : serialization_info (type: System.Runtime.Serialization.SerializationInfo)
				30 : generation (type: System.Int32)
    '''

    def __init__(self, pm, ptr, key_type_init, value_type_init):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self.keySlots = None
            self.valueSlots = None
            self.touchedSlots = 0
            return
        self.keySlots = Array(pm, pm.read_int(ptr + 0x10), key_type_init)
        self.valueSlots = Array(pm, pm.read_int(ptr + 0x14), value_type_init)
        self.touchedSlots = pm.read_int(ptr + 0x18)

    @property
    def value(self):
        result = {}
        _next = 0
        while (_next < self.touchedSlots):
            cur = _next
            try:
                key = self.keySlots.get(cur)
                value = self.valueSlots.get(cur)
                result[key] = value
            except Exception as e:
                pass
            _next += 1
        return result

    def print_tree(self, name=None, depth=0):
        tab = '  ' * depth
        name_str = f'{name}: ' if name else ''
        value = self.value
        print(f'{tab}{name_str}{self.__class__.__name__}({hex(self.ptr)}) = size({len(value)})')
        for key in value:
            v = value[key]
            if isinstance(v, BaseModel):
                v.print_tree(f'key({key})', depth + 1)
            else:
                print(f'{tab}  key({key}): {v}')


class SystemString(DataModel):
    '''
    66ad368 : System.String
        static fields
            0 : Empty (type: System.String)
            4 : WhiteChars (type: System.Char[])
        fields
            8 : length (type: System.Int32)
            c : start_char (type: System.Char)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self.length = 0
            self.start_char_ptr = 0x0
            return
        self.length = pm.read_int(ptr + 0x8)
        self.start_char_ptr = ptr + 0xc

    @property
    def value(self):
        if self.ptr == 0x0:
            return None
        chars = [
            chr(self.pm.read_ushort(self.start_char_ptr + 0x2 * i))
            for i in range(self.length)
        ]
        return ''.join(chars)


class CSteamID(DataModel):
    '''
    171d1b28 : Steamworks.CSteamID
        static fields
            0 : Nil (type: Steamworks.CSteamID)
            8 : OutofDateGS (type: Steamworks.CSteamID)
            10 : LanModeGS (type: Steamworks.CSteamID)
            18 : NotInitYetGS (type: Steamworks.CSteamID)
            20 : NonSteamGS (type: Steamworks.CSteamID)
        fields
            8 : m_SteamID (type: System.UInt64)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self.m_SteamID = None
            return
        self.m_SteamID = pm.read_ulonglong(ptr + 0x8)

    @property
    def value(self):
        return self.m_SteamID


class DataModelBool(DataModel):
    '''
    170328f8 : DataModelBool
        fields
            8 : valueChanged (type: System.Action<System.Boolean,System.Boolean>)
            c : _value (type: System.Boolean)
            d : _fireEventWhenSet (type: System.Boolean)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self._value = None
            return
        self._value = pm.read_bytes(ptr + 0xc, 1)

    @property
    def value(self):
        return self._value == b'\x01'


class DataModelString(DataModel):
    '''
    1702ba30 : DataModelString
        fields
            8 : valueChanged (type: System.Action<System.String,System.String>)
            c : _value (type: System.String)
            10 : _fireEventWhenSet (type: System.Boolean)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self._value = None
            return
        self._value = SystemString(pm, pm.read_int(ptr + 0xc))

    @property
    def value(self):
        return self._value.value


class DataModelInt(DataModel):
    '''
    1702cca8 : DataModelInt
        fields
            8 : valueChanged (type: System.Action<System.Int32,System.Int32>)
            c : maxValue (type: System.Int32)
            10 : minValue (type: System.Int32)
            14 : suppressEvents (type: System.Boolean)
            15 : locked (type: System.Boolean)
            18 : _value (type: System.Int32)
            1c : _fireEventWhenSet (type: System.Boolean)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self._value = None
            return
        self._value = pm.read_int(ptr + 0x18)

    @property
    def value(self):
        return self._value


class DataModelFloat(DataModel):
    '''
    1702cef8 : DataModelFloat
        fields
            8 : valueChanged (type: System.Action<System.Single,System.Single>)
            c : _value (type: System.Single)
            10 : _fireEventWhenSet (type: System.Boolean)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self._value = None
            return
        self._value = pm.read_float(ptr + 0xc)

    @property
    def value(self):
        return self._value


class DataModelList(BaseModel):
    '''
    17039198 : DataModelList
        fields
            8 : valueChanged (type: System.Action<System.Collections.Generic.List<System.String>,System.String>)
            10 : suppressEvents (type: System.Boolean)
            c : _list (type: System.Collections.Generic.List<System.String>)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self._list = None
            return
        self._list = GenericList(
            pm, ptr + 0xc,
            lambda inner_ptr: SystemString(pm, pm.read_int(inner_ptr)))

    def get(self, index):
        return self._list.get(index)


class UserManager(BaseModel):
    '''
    171a1d98 : UserManager
        fields
            c : initialize (type: System.Action)
            10 : userAdded (type: System.Action<IUser>)
            14 : userRemoved (type: System.Action<IUser>)
            18 : controllerDisconnect (type: System.Action)
            1c : returnToOS (type: System.Action)
            20 : _implementation (type: IUserManager) -> PCUserManager
            24 : _updating (type: System.Boolean)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self._implementation = None
            return
        self._implementation = PCUserManager(pm, pm.read_int(ptr + 0x20))


class PCUserManager(BaseModel):
    '''
    17a5c268 : PCUserManager
        fields
            8 : initialize (type: System.Action)
            c : userAdded (type: System.Action<IUser>)
            10 : userRemoved (type: System.Action<IUser>)
            14 : controllerDisconnect (type: System.Action)
            18 : returnToOS (type: System.Action)
            1c : _currentUser (type: IUser) -> PCSteamUser
            20 : _currentUserIdModel (type: DataModelString)
            24 : _users (type: IUser[]) -> Array(PCSteamUser)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self._currentUser = None
            self._users = None
            return
        self._currentUser = PCSteamUser(pm, pm.read_int(ptr + 0x1c))
        self._currentUserIdModel = DataModelString(pm, pm.read_int(ptr + 0x20))
        self._users = Array(
            pm, pm.read_int(ptr + 0x24),
            lambda inner_ptr: PCSteamUser(pm, pm.read_int(inner_ptr)))


class PCSteamUser(BaseModel):
    '''
    17a60028 : BaseUser
        fields
            8 : change (type: System.Action<IUser>)
            c : <gameStats>k__BackingField (type: GameStats)
            10 : _errorPopup (type: MessagePopup)
            14 : _name (type: System.String)
    19f44140 : PCSteamUser
        fields
            18 : _id (type: System.String)
            1c : _username (type: System.String)
            20 : _steamId (type: Steamworks.CSteamID)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self.gameStats = None
            self._name = None
            self._id = None
            self._username = None
            self._steamId = None
            return
        self.gameStats = GameStats(pm, pm.read_int(ptr + 0xc))
        self._name = SystemString(pm, pm.read_int(ptr + 0x14))
        self._id = SystemString(pm, pm.read_int(ptr + 0x18))
        self._username = SystemString(pm, pm.read_int(ptr + 0x1c))
        self._steamId = CSteamID(pm, pm.read_int(ptr + 0x20))


class SelectModel(BaseModel):
    '''
    66cb3d8 : SelectModel
        fields
            8 : <id>k__BackingField (type: System.String)
            c : <name>k__BackingField (type: System.String)
            10 : <resourceName>k__BackingField (type: System.String)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self.id = None
            self.name = None
            self.resourceName = None
            return
        self.id = SystemString(pm, pm.read_int(ptr + 0x8))
        self.name = SystemString(pm, pm.read_int(ptr + 0xc))
        self.resourceName = SystemString(pm, pm.read_int(ptr + 0x10))


class GameTypeFlowModel(SelectModel):
    '''
    66cb3d8 : SelectModel
        fields
            8 : <id>k__BackingField (type: System.String)
            c : <name>k__BackingField (type: System.String)
            10 : <resourceName>k__BackingField (type: System.String)
    17a73650 : GameTypeFlowModel
        fields
            14 : <factory>k__BackingField (type: AbstractGameTypeFlowFactory)
            18 : <selectable>k__BackingField (type: System.Boolean)
    '''

    ID_QUICK_MATCH = 'QUICK_MATCH'

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self.selectable = None
            return
        self.selectable = pm.read_bytes(ptr + 0x10, 1) == '\x01'

    def is_single_match(self):
        return self.name.value == self.ID_QUICK_MATCH


class GameTypeModel(SelectModel):
    '''
    66cb3d8 : SelectModel
        fields
            8 : <id>k__BackingField (type: System.String)
            c : <name>k__BackingField (type: System.String)
            10 : <resourceName>k__BackingField (type: System.String)
    17a7e2b8 : GameTypeModel
        fields
            14 : <worlds>k__BackingField (type: System.Collections.Generic.List<SelectModel>)
            18 : <type>k__BackingField (type: System.String)
            1c : <startState>k__BackingField (type: System.String)
    '''

    TYPE_SINGLE_PLAYER_LEADERBOARD = 'SINGLE_PLAYER_LEADERBOARD'
    TYPE_SINGLE_PLAYER = 'SINGLE_PLAYER'
    TYPE_MULTIPLAYER_ONLINE = 'MULTIPLAYER_ONLINE'
    TYPE_MULTIPLAYER_LOCAL = 'MULTIPLAYER_LOCAL'

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self.worlds = None
            self.type = None
            self.startState = None
            return
        self.worlds = GenericList(
            pm, pm.read_int(ptr + 0x14),
            lambda inner_ptr: SelectModel(pm, pm.read_int(inner_ptr)))
        self.type = SystemString(pm, pm.read_int(ptr + 0x18))
        self.startState = SystemString(pm, pm.read_int(ptr + 0x1c))

    def is_multiplayer(self):
        return self.type.value == self.TYPE_MULTIPLAYER_ONLINE or self.type.value == self.TYPE_MULTIPLAYER_LOCAL


class GameStats(BaseModel):
    '''
    17038db8 : GameStats
        fields
            8 : levelComplete (type: DataModelBool)
            c : levelId (type: DataModelString)
            10 : worldId (type: DataModelInt)
            14 : levelType (type: DataModelString)
            18 : levelWon (type: DataModelBool)
            1c : towerHeight (type: DataModelFloat)
            20 : brickCount (type: DataModelInt)
            24 : time (type: DataModelFloat)
            28 : fastestNormalRaceTime (type: DataModelFloat)
            2c : timesMagicUsed (type: DataModelInt)
            30 : roofUpsideDown (type: DataModelBool)
            34 : moonDropped (type: DataModelBool)
            38 : finished (type: DataModelBool)
            3c : bricksDropped (type: DataModelInt)
            40 : bricksPlaced (type: DataModelInt)
            44 : numberOfRotates (type: DataModelInt)
            48 : waveNumber (type: DataModelInt)
            4c : highestWaveNumber (type: DataModelInt)
            50 : primaryUser (type: DataModelString)
            54 : numPlayers (type: DataModelInt)
            58 : gameQuit (type: DataModelBool)
            5c : isHost (type: DataModelBool)
            60 : spellsUsed (type: DataModelList)
            64 : medalCount (type: DataModelInt)
            68 : health (type: DataModelInt)
            6c : maxIvyBricksConnected (type: DataModelInt)
            70 : bubblesStabilized (type: DataModelInt)
            74 : spellsPickedUp (type: DataModelInt)
            78 : timeLeft (type: DataModelFloat)
            7c : sessionCreated (type: DataModelBool)
            80 : sessionJoined (type: DataModelBool)
            84 : sessionTimedOut (type: DataModelBool)
            88 : sessionStarted (type: DataModelBool)
            8c : sessionFull (type: DataModelBool)
            90 : sessionJoinTryCount (type: DataModelInt)
            94 : eloScore (type: DataModelInt)
            98 : eloScoreBracket (type: DataModelInt)
            9c : eloScoreDelta (type: DataModelInt)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self.levelId = None
            self.worldId = None
            self.levelType = None
            self.levelWon = None
            self.towerHeight = None
            self.brickCount = None
            self.time = None
            self.fastestNormalRaceTime = None
            self.timesMagicUsed = None
            self.roofUpsideDown = None
            self.moonDropped = None
            self.finished = None
            self.bricksDropped = None
            self.bricksPlaced = None
            self.numberOfRotates = None
            self.waveNumber = None
            self.highestWaveNumber = None
            self.primaryUser = None
            self.numPlayers = None
            self.gameQuit = None
            self.isHost = None
            self.spellsUsed = None
            self.medalCount = None
            self.health = None
            self.maxIvyBricksConnected = None
            self.bubblesStabilized = None
            self.spellsPickedUp = None
            self.timeLeft = None
            self.sessionCreated = None
            self.sessionJoined = None
            self.sessionTimedOut = None
            self.sessionStarted = None
            self.sessionFull = None
            self.sessionJoinTryCount = None
            self.eloScore = None
            self.eloScoreBracket = None
            self.eloScoreDelta = None
            return
        self.levelComplete = DataModelBool(pm, pm.read_int(ptr + 0x8))
        self.levelId = DataModelString(pm, pm.read_int(ptr + 0xc))
        self.worldId = DataModelInt(pm, pm.read_int(ptr + 0x10))
        self.levelType = DataModelString(pm, pm.read_int(ptr + 0x14))
        self.levelWon = DataModelBool(pm, pm.read_int(ptr + 0x18))
        self.towerHeight = DataModelFloat(pm, pm.read_int(ptr + 0x1c))
        self.brickCount = DataModelInt(pm, pm.read_int(ptr + 0x20))
        self.time = DataModelFloat(pm, pm.read_int(ptr + 0x24))
        self.fastestNormalRaceTime = DataModelFloat(pm,
                                                    pm.read_int(ptr + 0x28))
        self.timesMagicUsed = DataModelInt(pm, pm.read_int(ptr + 0x2c))
        self.roofUpsideDown = DataModelBool(pm, pm.read_int(ptr + 0x30))
        self.moonDropped = DataModelBool(pm, pm.read_int(ptr + 0x34))
        self.finished = DataModelBool(pm, pm.read_int(ptr + 0x38))
        self.bricksDropped = DataModelInt(pm, pm.read_int(ptr + 0x3c))
        self.bricksPlaced = DataModelInt(pm, pm.read_int(ptr + 0x40))
        self.numberOfRotates = DataModelInt(pm, pm.read_int(ptr + 0x44))
        self.waveNumber = DataModelInt(pm, pm.read_int(ptr + 0x48))
        self.highestWaveNumber = DataModelInt(pm, pm.read_int(ptr + 0x4c))
        self.primaryUser = DataModelString(pm, pm.read_int(ptr + 0x50))
        self.numPlayers = DataModelInt(pm, pm.read_int(ptr + 0x54))
        self.gameQuit = DataModelBool(pm, pm.read_int(ptr + 0x58))
        self.isHost = DataModelBool(pm, pm.read_int(ptr + 0x5c))
        self.spellsUsed = DataModelList(pm, pm.read_int(ptr + 0x60))
        self.medalCount = DataModelInt(pm, pm.read_int(ptr + 0x64))
        self.health = DataModelInt(pm, pm.read_int(ptr + 0x68))
        self.maxIvyBricksConnected = DataModelInt(pm, pm.read_int(ptr + 0x6c))
        self.bubblesStabilized = DataModelInt(pm, pm.read_int(ptr + 0x70))
        self.spellsPickedUp = DataModelInt(pm, pm.read_int(ptr + 0x74))
        self.timeLeft = DataModelFloat(pm, pm.read_int(ptr + 0x78))
        self.sessionCreated = DataModelBool(pm, pm.read_int(ptr + 0x7c))
        self.sessionJoined = DataModelBool(pm, pm.read_int(ptr + 0x80))
        self.sessionTimedOut = DataModelBool(pm, pm.read_int(ptr + 0x84))
        self.sessionStarted = DataModelBool(pm, pm.read_int(ptr + 0x88))
        self.sessionFull = DataModelBool(pm, pm.read_int(ptr + 0x8c))
        self.sessionJoinTryCount = DataModelInt(pm, pm.read_int(ptr + 0x90))
        self.eloScore = DataModelInt(pm, pm.read_int(ptr + 0x94))
        self.eloScoreBracket = DataModelInt(pm, pm.read_int(ptr + 0x98))
        self.eloScoreDelta = DataModelInt(pm, pm.read_int(ptr + 0x9c))


class PlayerMatchResult(BaseModel):
    '''
    17a47ea8 : PlayerMatchResult
        fields
            8 : rank (type: System.Int32)
            c : difficulty (type: System.String)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self.rank = None
            self.difficulty = None
            return
        self.rank = pm.read_int(ptr + 0x8)
        self.difficulty = SystemString(pm, pm.read_int(ptr + 0xc))


class AbstractMultiplayerGameTypeFlowController(BaseModel):
    '''
    1716f6e0 : AbstractGameTypeFlowController
        fields
            8 : allowRetry (type: System.Boolean)
    17a99280 : AbstractMultiplayerGameTypeFlowController
        fields
            c : next (type: System.Action)
            10 : retry (type: System.Action)
            14 : quit (type: System.Action)
            18 : modeSelect (type: System.Action)
            24 : <finished>k__BackingField (type: System.Boolean)
            1c : _gameSetup (type: GameSetupData)
            20 : _inputs (type: System.String[])
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self.allowRetry = None
            self.finished = None
            return
        self.allowRetry = pm.read_bytes(ptr + 0x8, 1) == '\x01'
        self.finished = pm.read_bytes(ptr + 0x24, 1) == '\x01'


class CupMatchFlowController(AbstractMultiplayerGameTypeFlowController):
    '''
    1716f6e0 : AbstractGameTypeFlowController
        fields
            8 : allowRetry (type: System.Boolean)
    17a99280 : AbstractMultiplayerGameTypeFlowController
        fields
            c : next (type: System.Action)
            10 : retry (type: System.Action)
            14 : quit (type: System.Action)
            18 : modeSelect (type: System.Action)
            24 : <finished>k__BackingField (type: System.Boolean)
            1c : _gameSetup (type: GameSetupData)
            20 : _inputs (type: System.String[])
    17acae80 : CupMatchFlowController
        fields
            28 : _resultsByPlayer (type: System.Collections.Generic.Dictionary<System.String,System.Collections.Generic.List<PlayerMatchResult>>)
            2c : _controllerIds (type: System.Collections.Generic.List<System.String>)
            30 : _wizardIdsByPlayer (type: System.Collections.Generic.List<System.Int32>)
            60 : _targetScore (type: System.Int32)
            34 : _tournamentResultsPopup (type: TournamentResultsPopup)
            38 : _tournamentWinnerPopup (type: TournamentWinnerPopup)
            3c : _levelUpdatePopup (type: LevelUpdatePopup)
            40 : _winningGameController (type: AbstractGameController)
            44 : _gameModes (type: System.Collections.Generic.List<GameModeModel>)
            48 : _cupType (type: System.String)
            4c : _netPlayersStartup (type: System.Collections.Generic.List<NetPlayerAtStartup>)
            50 : _random (type: System.Random)
            64 : _defaultWin (type: System.Boolean)
            54 : _playerRanks (type: System.Collections.Generic.List<PlayerRankStruct>)
            65 : _autoNext (type: System.Boolean)
            58 : _gameType (type: System.String)
            5c : _ownRank (type: PlayerRankStruct)
            66 : _friendsMatch (type: System.Boolean)
            67 : _overtime (type: System.Boolean)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self._resultsByPlayer = None
            self._controllerIds = None
            self._wizardIdsByPlayer = None
            self._targetScore = None
            self._tournamentResultsPopup = None
            self._tournamentWinnerPopup = None
            self._levelUpdatePopup = None
            self._winningGameController = None
            self._gameModes = None
            self._cupType = None
            self._netPlayersStartup = None
            self._defaultWin = None
            self._playerRanks = None
            self._autoNext = None
            self._gameType = None
            self._ownRank = None
            self._friendsMatch = None
            self._overtime = None
            return
        self._resultsByPlayer = GenericDictionary(
            pm, ptr + 0x28,
            lambda inner_ptr: SystemString(pm, pm.read_int(inner_ptr)),
            lambda inner_ptr: GenericList(pm, pm.read_int(inner_ptr), lambda inner_ptr: PlayerMatchResult(pm, pm.read_int(inner_ptr))))
        self._controllerIds = GenericList(
            pm, pm.read_int(ptr + 0x2c),
            lambda inner_ptr: SystemString(pm, pm.read_int(inner_ptr)))
        self._wizardIdsByPlayer = GenericList(
            pm, pm.read_int(ptr + 0x2c),
            lambda inner_ptr: pm.read_int(inner_ptr))
        self._targetScore = pm.read_int(ptr + 0x60)
        # self._tournamentResultsPopup = TournamentResultsPopup(pm, pm.read_int(ptr + 0x34))
        # self._tournamentWinnerPopup = TournamentWinnerPopup(pm, pm.read_int(ptr + 0x38))
        # self._levelUpdatePopup = LevelUpdatePopup(pm, pm.read_int(ptr + 0x3c))
        # self._winningGameController = AbstractGameController(pm, pm.read_int(ptr + 0x40))
        # self._gameModes = GenericList(pm, pm.read_int(ptr + 0x44), lambda inner_ptr: GameModeModel(pm, pm.read_int(inner_ptr)))
        self._cupType = SystemString(pm, pm.read_int(ptr + 0x48))
        # self._netPlayersStartup = GenericList(pm, pm.read_int(ptr + 0x4c), lambda inner_ptr: NetPlayerAtStartup(pm, pm.read_int(inner_ptr)))
        self._defaultWin = pm.read_bytes(ptr + 0x64, 1) == '\x01'
        # self._playerRanks = GenericList(pm, pm.read_int(ptr + 0x54), lambda inner_ptr: PlayerRankStruct(pm, pm.read_int(inner_ptr)))
        self._autoNext = pm.read_bytes(ptr + 0x65, 1) == '\x01'
        self._gameType = SystemString(pm, pm.read_int(ptr + 0x58))
        # self._ownRank = PlayerRankStruct(pm, pm.read_int(ptr + 0x5c))
        self._friendsMatch = pm.read_bytes(ptr + 0x66, 1) == '\x01'
        self._overtime = pm.read_bytes(ptr + 0x67, 1) == '\x01'


class SingleLocalMatchFlowController(
        AbstractMultiplayerGameTypeFlowController):
    '''
    1716f6e0 : AbstractGameTypeFlowController
        fields
            8 : allowRetry (type: System.Boolean)
    17a99280 : AbstractMultiplayerGameTypeFlowController
        fields
            c : next (type: System.Action)
            10 : retry (type: System.Action)
            14 : quit (type: System.Action)
            18 : modeSelect (type: System.Action)
            24 : <finished>k__BackingField (type: System.Boolean)
            1c : _gameSetup (type: GameSetupData)
            20 : _inputs (type: System.String[])
    17a991c8 : SingleLocalMatchFlowController
        fields
            28 : _endGamePopup (type: EndGamePopup)
    '''
    pass


class SingleOnlineMatchFlowController(
        AbstractMultiplayerGameTypeFlowController):
    '''
    1716f6e0 : AbstractGameTypeFlowController
        fields
            8 : allowRetry (type: System.Boolean)
    17a99280 : AbstractMultiplayerGameTypeFlowController
        fields
            c : next (type: System.Action)
            10 : retry (type: System.Action)
            14 : quit (type: System.Action)
            18 : modeSelect (type: System.Action)
            24 : <finished>k__BackingField (type: System.Boolean)
            1c : _gameSetup (type: GameSetupData)
            20 : _inputs (type: System.String[])
    17ac8da0 : SingleOnlineMatchFlowController
    '''
    pass


class GameSetupData(BaseModel):
    '''
    1716e0e8 : GameSetupData
        fields
            8 : gameType (type: GameTypeModel)
            c : world (type: WorldModel)
            10 : gameMode (type: GameModeModel)
            14 : gameModes (type: System.Collections.Generic.List<GameModeModel>)
            18 : selectedWorld (type: System.String)
            1c : selectedType (type: System.String)
            20 : inputs (type: System.String[])
            24 : wizardIds (type: System.Int32[])
            28 : brickPacks (type: System.String[])
            2c : selectedWizardIds (type: System.Collections.Generic.Dictionary<System.Int32,System.Int32>)
            30 : selectedBrickPacks (type: System.Collections.Generic.Dictionary<System.Int32,System.String>)
            40 : retry (type: System.Boolean)
            41 : showModeTitle (type: System.Boolean)
            34 : gameTypeFlowModel (type: GameTypeFlowModel)
            38 : gameTypeFlow (type: AbstractGameTypeFlowController)
            44 : randomSeed (type: System.Int32)
            48 : inviteMode (type: GameSetupData.InviteMode)
            3c : inviteIds (type: System.String[])
            4c : privateGame (type: System.Boolean)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            return
        self.gameType = GameTypeModel(pm, pm.read_int(ptr + 0x8))
        # self.world = WorldModel(pm, pm.read_int(ptr + 0xc))
        # self.gameMode = GameModeModel(pm, pm.read_int(ptr + 0x10))
        # self.gameModes = GenericList(pm, pm.read_int(ptr + 0x14), lambda inner_ptr: GameModeModel(pm, pm.read_int(inner_ptr)))
        self.inputs = Array(
            pm, pm.read_int(ptr + 0x20),
            lambda inner_ptr: SystemString(pm, pm.read_int(inner_ptr)))
        self.wizardIds = Array(pm, pm.read_int(ptr + 0x24),
                               lambda inner_ptr: pm.read_int(inner_ptr))
        self.brickPacks = Array(
            pm, pm.read_int(ptr + 0x28),
            lambda inner_ptr: SystemString(pm, pm.read_int(inner_ptr)))
        self.selectedWizardIds = GenericDictionary(
            pm, pm.read_int(ptr + 0x2c),
            lambda inner_ptr: pm.read_int(inner_ptr),
            lambda inner_ptr: pm.read_int(inner_ptr))
        self.selectedBrickPacks = GenericDictionary(
            pm, pm.read_int(ptr + 0x30),
            lambda inner_ptr: pm.read_int(inner_ptr),
            lambda inner_ptr: SystemString(pm, pm.read_int(inner_ptr)))
        self.retry = pm.read_bytes(ptr + 0x40, 1) == b'\x01'
        self.showModeTitle = pm.read_bytes(ptr + 0x41, 1) == b'\x01'
        self.gameTypeFlowModel = GameTypeFlowModel(pm, pm.read_int(ptr + 0x34))

        _GameTypeFlowController = None
        if self.gameType.is_multiplayer():
            if self.gameTypeFlowModel.is_single_match():
                if self.gameType.type == GameTypeModel.TYPE_MULTIPLAYER_LOCAL:
                    _GameTypeFlowController = SingleLocalMatchFlowController
                else:
                    _GameTypeFlowController = SingleOnlineMatchFlowController
            else:
                _GameTypeFlowController = CupMatchFlowController

        print(self.gameType.is_multiplayer())

        if _GameTypeFlowController:
            self.gameTypeFlow = _GameTypeFlowController(
                pm, pm.read_int(ptr + 0x38))
        else:
            self.gameTypeFlow = None

        self.randomSeed = pm.read_int(ptr + 0x44)
        # self.inviteMode = GameSetupDataInviteMode(pm, pm.read_int(ptr + 0x48))
        self.inviteIds = Array(
            pm, pm.read_int(ptr + 0x3c),
            lambda inner_ptr: SystemString(pm, pm.read_int(inner_ptr)))
        self.privateGame = pm.read_bytes(ptr + 0x4c, 1) == b'\x01'


class GameStateController(BaseModel):
    '''
    1716d758 : AbstractStateController
        fields
            8 : _stateFlowController (type: StateFlowController)
    1716d6a0 : AbstractBricksStateController
        fields
            c : _sceneName (type: System.String)
            10 : _nextState (type: System.String)
            14 : _nextGameSetup (type: System.Object)
            18 : _transitionEffect (type: TransitionEffect)
            1c : _autoTransitionIn (type: System.Boolean)
            1d : _transitionInStarted (type: System.Boolean)
            1e : _transitionOutStarted (type: System.Boolean)
            1f : _transitionOutCompleted (type: System.Boolean)
    17a74f30 : GameStateController
        fields
            20 : _gameTypeController (type: AbstractGameTypeController)
            24 : _gameSetup (type: GameSetupData)
            28 : _updateHelper (type: UnityEngine.GameObject)
            2c : _updateHandler (type: UpdateHandler)
            30 : _gameMode (type: AbstractGameMode)
            34 : _creditsPopup (type: CreditsPopup)
            38 : _playerStats (type: PlayerStats)
            3c : _networkErrorPopup (type: MessagePopup)
            40 : _networkError (type: System.Boolean)
            44 : _frameCount (type: System.Int32)
            48 : _started (type: System.Boolean)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if ptr == 0x0:
            self._gameSetup = None
            return
        self._gameSetup = GameSetupData(pm, pm.read_int(ptr + 0x24))