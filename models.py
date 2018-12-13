#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BaseModel:
    def __init__(self, pm, ptr):
        self.pm = pm
        self.ptr = ptr
        # print(f'{self.__class__.__name__}({hex(self.ptr)})')

    @classmethod
    def attrs(cls):
        return ['ptr']

    def unpack(self, v):
        return v.serialize() if isinstance(v, BaseModel) else v

    def print_tree(self, name=None, depth=0):
        tab = '  ' * depth
        name_str = f'{name}: ' if name else ''
        print(f'{tab}{name_str}{self.__class__.__name__}({hex(self.ptr)})')
        for attr_name in self.attrs():
            if not hasattr(self, attr_name):
                print(f'{tab}  {attr_name}: !NOT_PARSED')
            else:
                attr = getattr(self, attr_name)
                if isinstance(attr, BaseModel):
                    attr.print_tree(attr_name, depth + 1)
                else:
                    print(f'{tab}  {attr_name}: {attr}')

    def serialize(self):
        obj = {}
        for attr_name in self.attrs():
            if hasattr(self, attr_name):
                attr = getattr(self, attr_name)
                obj[attr_name] = self.unpack(attr)
        return obj

    def is_initialized(self):
        '''아마도 동작할 것'''
        return self.ptr != 0x0 and self.pm.read_uint(self.ptr + 0x4) == 0


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
        print(f'{tab}{name_str}{self.value}')

    def serialize(self):
        return self.unpack(self.value)


class ListModel(BaseModel):
    def get(self, index):
        raise NotImplementedError()

    @property
    def length(self):
        raise NotImplementedError()

    def print_tree(self, name=None, depth=0):
        tab = '  ' * depth
        name_str = f'{name}: ' if name else ''
        print(
            f'{tab}{name_str}{self.__class__.__name__}({hex(self.ptr)}) = length({self.length})'
        )
        for i in range(self.length):
            v = self.get(i)
            if isinstance(v, BaseModel):
                v.print_tree(f'index({i})', depth + 1)
            else:
                print(f'{tab}  index({i}): {v}')

    def serialize(self):
        return [self.unpack(self.get(i)) for i in range(self.length)]


class Array(ListModel):
    def __init__(self, pm, ptr, _type_init, item_size=None):
        super().__init__(pm, ptr)
        if item_size is None:
            item_size = 0x4
        if not self.is_initialized():
            self._size = 0
            self._first_ptr = 0
            return
        self._size = pm.read_int(ptr + 0xc)
        self._type_init = _type_init
        self.item_size = item_size
        self._first_ptr = ptr + 0x10

    def index_ptr(self, index):
        return self._first_ptr + self.item_size * index

    def get(self, index):
        return self._type_init(self.index_ptr(index))

    @property
    def length(self):
        return self._size


class GenericLink(BaseModel):
    '''
    !! THIS IS JUST STRUCT. IGNORE BELOW !!
    17b060f0 : System.Collections.Generic.Link
        fields
            8 : HashCode (type: System.Int32)
            c : Next (type: System.Int32)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if not self.is_initialized():
            self.HashCode = None
            self.Next = None
            return
        self.HashCode = pm.read_int(ptr + 0x0)
        self.Next = pm.read_int(ptr + 0x4)

    def is_initialized(self):
        return True

    @classmethod
    def attrs(cls):
        return super().attrs() + ['HashCode', 'Next']


class GenericList(ListModel):
    '''
    6782578 : System.Collections.Generic.List`1[T]
        static fields
            0 : EmptyArray (type: T[])
        fields
            8 : _items (type: T[])
            c : _size (type: System.Int32)
            10 : _version (type: System.Int32)
    '''

    def __init__(self, pm, ptr, _type_init, item_size=None):
        super().__init__(pm, ptr)
        if item_size is None:
            item_size = 0x4
        if not self.is_initialized():
            self._items = None
            self._size = 0
            self._version = None
            return
        self._items = Array(pm, pm.read_int(ptr + 0x8), _type_init, item_size)
        self._size = pm.read_int(ptr + 0xc)
        self._version = pm.read_int(ptr + 0x10)

    def get(self, index):
        return self._items.get(index)

    @property
    def length(self):
        return self._size


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

    HASH_FLAG = -2147483648

    def __init__(self, pm, ptr, key_type_init, value_type_init):
        super().__init__(pm, ptr)
        if not self.is_initialized():
            self.linkSlots = None
            self.keySlots = None
            self.valueSlots = None
            self.touchedSlots = 0
            self.cached_data = None
            return
        self.linkSlots = Array(pm, pm.read_int(ptr + 0xc),
                               lambda inner_ptr: GenericLink(pm, inner_ptr),
                               0x8)
        self.keySlots = Array(pm, pm.read_int(ptr + 0x10), key_type_init)
        self.valueSlots = Array(pm, pm.read_int(ptr + 0x14), value_type_init)
        self.touchedSlots = pm.read_int(ptr + 0x18)
        self.cached_data = None

    @property
    def value(self):
        if not self.is_initialized():
            return None
        if self.cached_data:
            return self.cached_data
        self.cached_data = {}
        _next = 0
        while _next < self.touchedSlots:
            cur = _next
            if self.linkSlots.get(cur).is_initialized(
            ) and self.linkSlots.get(cur).HashCode & self.HASH_FLAG != 0:
                key = self.keySlots.get(cur)
                value = self.valueSlots.get(cur)
                self.cached_data[key] = value
            _next += 1
        return self.cached_data

    def print_tree(self, name=None, depth=0):
        tab = '  ' * depth
        name_str = f'{name}: ' if name else ''
        value = self.value
        if not self.is_initialized():
            print(f'{tab}{name_str}{value}')
            return
        print(
            f'{tab}{name_str}{self.__class__.__name__}({hex(self.ptr)}) = size({len(value)})'
        )
        for key in value:
            key_str = key
            if isinstance(key, DataModel):
                key_str = key.value
            v = value[key]
            if isinstance(v, BaseModel):
                v.print_tree(f'key({key_str})', depth + 1)
            else:
                print(f'{tab}  key({key_str}): {v}')

    def serialize(self):
        return {self.unpack(k): self.unpack(v) for k, v in self.value.items()}


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
        if not self.is_initialized():
            self.length = 0
            self.start_char_ptr = 0x0
            return
        self.length = pm.read_int(ptr + 0x8)
        self.start_char_ptr = ptr + 0xc

    @property
    def value(self):
        if not self.is_initialized():
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
        if not self.is_initialized():
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
        if not self.is_initialized():
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
        if not self.is_initialized():
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
        if not self.is_initialized():
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
        if not self.is_initialized():
            self._value = None
            return
        self._value = pm.read_float(ptr + 0xc)

    @property
    def value(self):
        return self._value


class DataModelList(ListModel):
    '''
    17039198 : DataModelList
        fields
            8 : valueChanged (type: System.Action<System.Collections.Generic.List<System.String>,System.String>)
            10 : suppressEvents (type: System.Boolean)
            c : _list (type: System.Collections.Generic.List<System.String>)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if not self.is_initialized():
            self._list = None
            return
        self._list = GenericList(
            pm, ptr + 0xc,
            lambda inner_ptr: SystemString(pm, pm.read_int(inner_ptr)))

    def get(self, index):
        return self._list.get(index)

    @property
    def length(self):
        return self._list.length()


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
        if not self.is_initialized():
            self._implementation = None
            return
        self._implementation = PCUserManager(pm, pm.read_int(ptr + 0x20))

    @classmethod
    def attrs(cls):
        return super().attrs() + ['_implementation']


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
        if not self.is_initialized():
            self._currentUser = None
            self._currentUserIdModel = None
            self._users = None
            return
        self._currentUser = PCSteamUser(pm, pm.read_int(ptr + 0x1c))
        self._currentUserIdModel = DataModelString(pm, pm.read_int(ptr + 0x20))
        self._users = Array(
            pm, pm.read_int(ptr + 0x24),
            lambda inner_ptr: PCSteamUser(pm, pm.read_int(inner_ptr)))

    @classmethod
    def attrs(cls):
        return super().attrs() + [
            '_currentUser', '_currentUserIdModel', '_users'
        ]


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
        if not self.is_initialized():
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

    @classmethod
    def attrs(cls):
        return super().attrs() + [
            'gameStats', '_name', '_id', '_username', '_steamId'
        ]


class TournamentResultsItem(BaseModel):
    '''
    17a47c68 : TournamentResultsItem
        fields
            8 : requestEffect (type: System.Action<AbstractEffect>)
            c : showWinnerComplete (type: System.Action)
            10 : skin (type: UnityEngine.GameObject)
            34 : _targetScore (type: System.Int32)
            14 : _medalContainer (type: UnityEngine.GameObject)
            18 : _rankings (type: System.Collections.Generic.List<PlayerMatchResult>)
            1c : _playerName (type: System.String)
            38 : _wizardId (type: System.Int32)
            3c : _overtimeMedals (type: System.Int32)
            20 : _overtimeLabel (type: TMPro.TextMeshProUGUI)
            24 : _cupType (type: System.String)
            40 : _cupWon (type: System.Boolean)
            41 : _online (type: System.Boolean)
            42 : _animateMedals (type: System.Boolean)
            28 : _trophy (type: UnityEngine.GameObject)
            2c : _userData (type: System.Object)
            30 : _avatarComponent (type: AvatarComponent)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if not self.is_initialized():
            self._targetScore = None
            self._rankings = None
            self._playerName = None
            self._wizardId = None
            self._overtimeMedals = None
            self._cupType = None
            self._cupWon = None
            self._online = None
            self._animateMedals = None
            return
        self._targetScore = pm.read_int(ptr + 0x34)
        self._rankings = GenericList(
            pm, ptr + 0x18,
            lambda inner_ptr: PlayerMatchResult(pm, pm.read_int(inner_ptr)))
        self._playerName = SystemString(pm, pm.read_int(ptr + 0x1c))
        self._wizardId = pm.read_int(ptr + 0x38)
        self._overtimeMedals = pm.read_int(ptr + 0x38)
        self._cupType = SystemString(pm, pm.read_int(ptr + 0x24))
        self._cupWon = pm.read_bytes(ptr + 0x40, 1) == '\x01'
        self._online = pm.read_bytes(ptr + 0x41, 1) == '\x01'
        self._animateMedals = pm.read_bytes(ptr + 0x42, 1) == '\x01'

    @classmethod
    def attrs(cls):
        return super().attrs() + [
            '_targetScore', '_rankings', '_playerName', '_wizardId',
            '_overtimeMedals', '_cupType', '_cupWon', '_online',
            '_animateMedals'
        ]


class BasePopup(BaseModel):
    '''
    1702eea0 : BasePopup
        fields
            8 : close (type: System.Action<BasePopup>)
            c : <skin>k__BackingField (type: UnityEngine.GameObject)
            10 : _inputLayer (type: InputActionLayer)
            14 : _container (type: UnityEngine.GameObject)
            18 : _tweener (type: DG.Tweening.Tweener)
            1c : _canvasGroup (type: UnityEngine.CanvasGroup)
            20 : _popupPosition (type: UnityEngine.RectTransform)
            24 : _autoCleanup (type: System.Boolean)
            25 : _useMoveInTween (type: System.Boolean)
            26 : _cursorWasVisible (type: System.Boolean)
            27 : _showCursor (type: System.Boolean)
    '''
    pass


class AbstractTournamentResultsPopup(BasePopup):
    '''
    1702eea0 : BasePopup
        fields
            8 : close (type: System.Action<BasePopup>)
            c : <skin>k__BackingField (type: UnityEngine.GameObject)
            10 : _inputLayer (type: InputActionLayer)
            14 : _container (type: UnityEngine.GameObject)
            18 : _tweener (type: DG.Tweening.Tweener)
            1c : _canvasGroup (type: UnityEngine.CanvasGroup)
            20 : _popupPosition (type: UnityEngine.RectTransform)
            24 : _autoCleanup (type: System.Boolean)
            25 : _useMoveInTween (type: System.Boolean)
            26 : _cursorWasVisible (type: System.Boolean)
            27 : _showCursor (type: System.Boolean)
    17a70a30 : AbstractTournamentResultsPopup
        fields
            28 : next (type: System.Action)
            2c : _tournamentResults (type: System.Collections.Generic.Dictionary<System.String,System.Collections.Generic.List<PlayerMatchResult>>)
            30 : _tournamentResultItems (type: System.Collections.Generic.Dictionary<System.String,TournamentResultsItem>)
            34 : _controllerIds (type: System.Collections.Generic.List<System.String>)
            58 : _targetScore (type: System.Int32)
            38 : _playerInfo (type: UnityEngine.GameObject)
            3c : _confirmButton (type: UnityEngine.GameObject)
            40 : _effectRunner (type: EffectRunner)
            44 : _updateHandler (type: UpdateHandler)
            48 : _wizardIds (type: System.Collections.Generic.List<System.Int32>)
            4c : _winningControllerId (type: System.String)
            50 : _cupType (type: System.String)
            5c : _animationCompleted (type: System.Boolean)
            54 : _netPlayers (type: System.Collections.Generic.List<NetPlayerAtStartup>)
    17a7e070 : TournamentResultsPopup
        fields
            64 : _autoNext (type: System.Boolean)
            60 : _mouseEventHandler (type: MouseEventHandler)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if not self.is_initialized():
            self._tournamentResults = None
            self._tournamentResultItems = None
            self._controllerIds = None
            self._targetScore = None
            self._wizardIds = None
            self._winningControllerId = None
            self._cupType = None
            self._animationCompleted = None
            self._netPlayers = None
            return
        self._tournamentResults = GenericDictionary(
            pm, pm.read_int(ptr + 0x2c),
            lambda inner_ptr: SystemString(pm, pm.read_int(inner_ptr)),
            lambda inner_ptr: GenericList(pm, pm.read_int(inner_ptr), lambda inner_inner_ptr: PlayerMatchResult(pm, inner_inner_ptr), 0x8))
        self._tournamentResultItems = GenericDictionary(
            pm, pm.read_int(ptr + 0x30),
            lambda inner_ptr: SystemString(pm, pm.read_int(inner_ptr)),
            lambda inner_ptr: TournamentResultsItem(pm, pm.read_int(inner_ptr))
        )
        self._controllerIds = GenericList(
            pm, ptr + 0x34,
            lambda inner_ptr: SystemString(pm, pm.read_int(inner_ptr)))
        self._targetScore = pm.read_int(ptr + 0x58)
        # self._wizardIds = GenericList(
        #     pm, ptr + 0x48,
        #     lambda inner_ptr: pm.read_int(inner_ptr))
        self._winningControllerId = SystemString(pm, pm.read_int(ptr + 0x4c))
        self._cupType = SystemString(pm, pm.read_int(ptr + 0x50))
        self._animationCompleted = pm.read_bytes(ptr + 0x5c, 1) == '\x01'
        self._netPlayers = GenericList(
            pm, ptr + 0x54,
            lambda inner_ptr: NetPlayerAtStartup(pm, pm.read_int(inner_ptr)))

    @classmethod
    def attrs(cls):
        return super().attrs() + [
            '_tournamentResults', '_tournamentResultItems', '_controllerIds',
            '_targetScore', '_wizardIds', '_winningControllerId', '_cupType',
            '_animationCompleted', '_netPlayers'
        ]


class TournamentResultsPopup(AbstractTournamentResultsPopup):
    '''
    1702eea0 : BasePopup
        fields
            8 : close (type: System.Action<BasePopup>)
            c : <skin>k__BackingField (type: UnityEngine.GameObject)
            10 : _inputLayer (type: InputActionLayer)
            14 : _container (type: UnityEngine.GameObject)
            18 : _tweener (type: DG.Tweening.Tweener)
            1c : _canvasGroup (type: UnityEngine.CanvasGroup)
            20 : _popupPosition (type: UnityEngine.RectTransform)
            24 : _autoCleanup (type: System.Boolean)
            25 : _useMoveInTween (type: System.Boolean)
            26 : _cursorWasVisible (type: System.Boolean)
            27 : _showCursor (type: System.Boolean)
    17a70a30 : AbstractTournamentResultsPopup
        fields
            28 : next (type: System.Action)
            2c : _tournamentResults (type: System.Collections.Generic.Dictionary<System.String,System.Collections.Generic.List<PlayerMatchResult>>)
            30 : _tournamentResultItems (type: System.Collections.Generic.Dictionary<System.String,TournamentResultsItem>)
            34 : _controllerIds (type: System.Collections.Generic.List<System.String>)
            58 : _targetScore (type: System.Int32)
            38 : _playerInfo (type: UnityEngine.GameObject)
            3c : _confirmButton (type: UnityEngine.GameObject)
            40 : _effectRunner (type: EffectRunner)
            44 : _updateHandler (type: UpdateHandler)
            48 : _wizardIds (type: System.Collections.Generic.List<System.Int32>)
            4c : _winningControllerId (type: System.String)
            50 : _cupType (type: System.String)
            5c : _animationCompleted (type: System.Boolean)
            54 : _netPlayers (type: System.Collections.Generic.List<NetPlayerAtStartup>)
    17a7e070 : TournamentResultsPopup
        fields
            64 : _autoNext (type: System.Boolean)
            60 : _mouseEventHandler (type: MouseEventHandler)
    '''
    pass


class TournamentCurrentScorePopup(AbstractTournamentResultsPopup):
    '''
    1702eea0 : BasePopup
        fields
            8 : close (type: System.Action<BasePopup>)
            c : <skin>k__BackingField (type: UnityEngine.GameObject)
            10 : _inputLayer (type: InputActionLayer)
            14 : _container (type: UnityEngine.GameObject)
            18 : _tweener (type: DG.Tweening.Tweener)
            1c : _canvasGroup (type: UnityEngine.CanvasGroup)
            20 : _popupPosition (type: UnityEngine.RectTransform)
            24 : _autoCleanup (type: System.Boolean)
            25 : _useMoveInTween (type: System.Boolean)
            26 : _cursorWasVisible (type: System.Boolean)
            27 : _showCursor (type: System.Boolean)
    17a70a30 : AbstractTournamentResultsPopup
        fields
            28 : next (type: System.Action)
            2c : _tournamentResults (type: System.Collections.Generic.Dictionary<System.String,System.Collections.Generic.List<PlayerMatchResult>>)
            30 : _tournamentResultItems (type: System.Collections.Generic.Dictionary<System.String,TournamentResultsItem>)
            34 : _controllerIds (type: System.Collections.Generic.List<System.String>)
            58 : _targetScore (type: System.Int32)
            38 : _playerInfo (type: UnityEngine.GameObject)
            3c : _confirmButton (type: UnityEngine.GameObject)
            40 : _effectRunner (type: EffectRunner)
            44 : _updateHandler (type: UpdateHandler)
            48 : _wizardIds (type: System.Collections.Generic.List<System.Int32>)
            4c : _winningControllerId (type: System.String)
            50 : _cupType (type: System.String)
            5c : _animationCompleted (type: System.Boolean)
            54 : _netPlayers (type: System.Collections.Generic.List<NetPlayerAtStartup>)
    17a70978 : TournamentCurrentScorePopup
        fields
            60 : _open (type: System.Boolean)
            64 : _previousPlayerCount (type: System.Int32)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if not self.is_initialized():
            self._open = None
            self._previousPlayerCount = None
            return

        self._open = pm.read_bytes(ptr + 0x60, 1) == '\x01'
        self._previousPlayerCount = pm.read_int(ptr + 0x64)

    @classmethod
    def attrs(cls):
        return super().attrs() + ['_open', '_previousPlayerCount']


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
        if not self.is_initialized():
            self.id = None
            self.name = None
            self.resourceName = None
            return
        self.id = SystemString(pm, pm.read_int(ptr + 0x8))
        self.name = SystemString(pm, pm.read_int(ptr + 0xc))
        self.resourceName = SystemString(pm, pm.read_int(ptr + 0x10))

    @classmethod
    def attrs(cls):
        return super().attrs() + ['id', 'name', 'resourceName']


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
        if not self.is_initialized():
            self.selectable = None
            return
        self.selectable = pm.read_bytes(ptr + 0x10, 1) == '\x01'

    def is_single_match(self):
        return self.name.value == self.ID_QUICK_MATCH

    @classmethod
    def attrs(cls):
        return super().attrs() + ['selectable']


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
        if not self.is_initialized():
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

    def is_online_multiplayer(self):
        return self.type.value == self.TYPE_MULTIPLAYER_ONLINE

    @classmethod
    def attrs(cls):
        return super().attrs() + ['worlds', 'type', 'startState']


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
        if not self.is_initialized():
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

    @classmethod
    def attrs(cls):
        return super().attrs() + [
            'levelId', 'worldId', 'levelType', 'levelWon', 'towerHeight',
            'brickCount', 'time', 'fastestNormalRaceTime', 'timesMagicUsed',
            'roofUpsideDown', 'moonDropped', 'finished', 'bricksDropped',
            'bricksPlaced', 'numberOfRotates', 'waveNumber',
            'highestWaveNumber', 'primaryUser', 'numPlayers', 'gameQuit',
            'isHost', 'spellsUsed', 'medalCount', 'health',
            'maxIvyBricksConnected', 'bubblesStabilized', 'spellsPickedUp',
            'timeLeft', 'sessionCreated', 'sessionJoined', 'sessionTimedOut',
            'sessionStarted', 'sessionFull', 'sessionJoinTryCount', 'eloScore',
            'eloScoreBracket', 'eloScoreDelta'
        ]


class PlayerMatchResult(BaseModel):
    '''
    !! THIS IS JUST STRUCT. IGNORE BELOW !!
    17a47ea8 : PlayerMatchResult
        fields
            8 : rank (type: System.Int32)
            c : difficulty (type: System.String)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if not self.is_initialized():
            self.rank = None
            self.difficulty = None
            return
        self.rank = pm.read_int(ptr + 0x0)
        self.difficulty = SystemString(pm, pm.read_int(ptr + 0x4))

    def is_initialized(self):
        return True

    @classmethod
    def attrs(cls):
        return super().attrs() + ['rank', 'difficulty']


class WorldModel(SelectModel):
    '''
    66cb3d8 : SelectModel
        fields
            8 : <id>k__BackingField (type: System.String)
            c : <name>k__BackingField (type: System.String)
            10 : <resourceName>k__BackingField (type: System.String)
    1718c818 : WorldModel
        static fields
            0 : ANY (type: WorldModel)
        fields
            14 : type (type: System.String)
            18 : <gameModes>k__BackingField (type: System.Collections.Generic.List<SelectModel>)
            1c : <medalCost>k__BackingField (type: System.Int32)
            20 : unlocked (type: System.Boolean)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if not self.is_initialized():
            self.type = None
            self.gameModes = None
            self.medalCost = None
            self.unlocked = None
            return
        self.type = SystemString(pm, pm.read_int(ptr + 0x14))
        self.gameModes = GenericList(
            pm, pm.read_int(ptr + 0x18),
            lambda inner_ptr: SelectModel(pm, pm.read_int(inner_ptr)))
        self.medalCost = pm.read_int(ptr + 0x1c)
        self.unlocked = pm.read_bytes(ptr + 0x20, 1) == '\x01'

    @classmethod
    def attrs(cls):
        return super().attrs() + ['type', 'gameModes', 'medalCost', 'unlocked']


class GameModeModel(SelectModel):
    '''
    66cb3d8 : SelectModel
        fields
            8 : <id>k__BackingField (type: System.String)
            c : <name>k__BackingField (type: System.String)
            10 : <resourceName>k__BackingField (type: System.String)
    1718c6e0 : GameModeModel
        fields
            14 : <gameModeFactory>k__BackingField (type: AbstractGameModeFactory)
            18 : <explanationId>k__BackingField (type: System.String)
            1c : <type>k__BackingField (type: System.String)
            20 : parentWorld (type: WorldModel)
            24 : menuBackgroundFactory (type: BackgroundsFactory)
    '''

    TYPE_MULTIPLAYER_RACE_EASY = 'MULTIPLAYER_RACE_EASY'
    TYPE_MULTIPLAYER_RACE_NORMAL = 'MULTIPLAYER_RACE_NORMAL'
    TYPE_MULTIPLAYER_RACE_PRO = 'MULTIPLAYER_RACE_PRO'
    TYPE_MULTIPLAYER_SURVIVAL_EASY = 'MULTIPLAYER_SURVIVAL_EASY'
    TYPE_MULTIPLAYER_SURVIVAL_NORMAL = 'MULTIPLAYER_SURVIVAL_NORMAL'
    TYPE_MULTIPLAYER_SURVIVAL_PRO = 'MULTIPLAYER_SURVIVAL_PRO'
    TYPE_MULTIPLAYER_PUZZLE_EASY = 'MULTIPLAYER_PUZZLE_EASY'
    TYPE_MULTIPLAYER_PUZZLE_NORMAL = 'MULTIPLAYER_PUZZLE_NORMAL'
    TYPE_MULTIPLAYER_PUZZLE_PRO = 'MULTIPLAYER_PUZZLE_PRO'

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if not self.is_initialized():
            self.explanationId = None
            self.type = None
            self.parentWorld = None
            return
        self.explanationId = SystemString(pm, pm.read_int(ptr + 0x18))
        self.type = SystemString(pm, pm.read_int(ptr + 0x1c))
        self.parentWorld = WorldModel(pm, pm.read_int(ptr + 0x20))

    @classmethod
    def attrs(cls):
        return super().attrs() + ['explanationId', 'type', 'parentWorld']


class NetPlayer(BaseModel):
    '''
    17030f40 : NetPlayer
        static fields
            0 : create (type: System.Action<NetPlayer>)
            4 : destroy (type: System.Action<NetPlayer>)
            8 : players (type: System.Collections.Generic.List<NetPlayer>)
            c : _netIdPlayerIds (type: System.Collections.Generic.Dictionary<System.UInt32,System.String>)
            10 : kCmdCmd_SpawnResource (type: System.Int32)
            14 : kCmdCmd_SpawnTowerPiece (type: System.Int32)
            18 : kCmdCmd_SetReady (type: System.Int32)
            1c : kCmdCmd_SetStatus (type: System.Int32)
            20 : kCmdCmd_SetUserName (type: System.Int32)
            24 : kCmdCmd_SetWizardId (type: System.Int32)
            28 : kCmdCmd_SetBrickPackId (type: System.Int32)
            2c : kCmdCmd_SetEloScore (type: System.Int32)
            30 : kCmdCmd_SetLevel (type: System.Int32)
            34 : kCmdCmd_SetSteamId (type: System.Int32)
        fields
            1c : statusChange (type: System.Action)
            20 : usernameChange (type: System.Action)
            24 : levelChanged (type: System.Action)
            28 : wizardIdChange (type: System.Action)
            2c : brickPackIdChange (type: System.Action)
            30 : steamIdChanged (type: System.Action)
            34 : objectSpawn (type: System.Action<NetPlayer,UnityEngine.GameObject,System.String>)
            38 : towerPieceSpawn (type: System.Action<NetPlayer,System.String,UnityEngine.Vector3>)
            3c : _id (type: System.String)
            4c : <destroying>k__BackingField (type: System.Boolean)
            50 : numActionsLastGame (type: System.Int32)
            40 : _user (type: IUser) -> PCSteamUser
            44 : _username (type: System.String)
            54 : _status (type: System.Int32)
            58 : _wizardId (type: System.Int32)
            48 : _brickPackId (type: System.String)
            5c : _level (type: System.Int32)
            60 : _steamId (type: System.UInt64)
            68 : _eloScore (type: System.Int32)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if not self.is_initialized():
            self._id = None
            self.destroying = None
            self.numActionsLastGame = None
            self._user = None
            self._username = None
            self._status = None
            self._wizardId = None
            self._brickPackId = None
            self._level = None
            self._steamId = None
            self._eloScore = None
            return
        self._id = SystemString(pm, pm.read_int(ptr + 0x3c))
        self.destroying = pm.read_bytes(ptr + 0x4c, 1) == '\x01'
        self.numActionsLastGame = pm.read_int(ptr + 0x50)
        self._user = PCSteamUser(pm, pm.read_int(ptr + 0x40))
        self._username = SystemString(pm, pm.read_int(ptr + 0x44))
        self._status = pm.read_int(ptr + 0x54)
        self._wizardId = pm.read_int(ptr + 0x58)
        self._brickPackId = SystemString(pm, pm.read_int(ptr + 0x48))
        self._level = pm.read_int(ptr + 0x5c)
        self._steamId = pm.read_ulonglong(ptr + 0x60)
        self._eloScore = pm.read_int(ptr + 0x68)

    @classmethod
    def attrs(cls):
        return super().attrs() + [
            '_id', 'destroying', 'numActionsLastGame', '_user', '_username',
            '_status', '_wizardId', '_brickPackId', '_level', '_steamId',
            '_eloScore'
        ]


class NetPlayerAtStartup(BaseModel):
    '''
    171a7a58 : NetPlayerAtStartup
        fields
            8 : <netPlayer>k__BackingField (type: NetPlayer)
            c : <username>k__BackingField (type: System.String)
            14 : <wizardId>k__BackingField (type: System.Int32)
            18 : <level>k__BackingField (type: System.Int32)
            1c : <eloScore>k__BackingField (type: System.Int32)
            10 : <id>k__BackingField (type: System.String)
            20 : <steamId>k__BackingField (type: System.UInt64)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if not self.is_initialized():
            self.netPlayer = None
            self.username = None
            self.wizardId = None
            self.level = None
            self.eloScore = None
            self.id = None
            self.steamId = None
            return
        self.netPlayer = NetPlayer(pm, pm.read_int(ptr + 0x8))
        self.username = SystemString(pm, pm.read_int(ptr + 0xc))
        self.wizardId = pm.read_int(ptr + 0x14)
        self.level = pm.read_int(ptr + 0x18)
        self.eloScore = pm.read_int(ptr + 0x1c)
        self.id = SystemString(pm, pm.read_int(ptr + 0x10))
        self.steamId = pm.read_ulonglong(ptr + 0x20)

    @classmethod
    def attrs(cls):
        return super().attrs() + [
            'netPlayer', 'username', 'wizardId', 'level', 'eloScore', 'id',
            'steamId'
        ]


class PlayerRankStruct(BaseModel):
    '''
    17197c88 : PlayerRankStruct
        fields
            8 : player (type: NetPlayer)
            c : rank (type: System.Int32)
            10 : experience (type: System.Int32)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if not self.is_initialized():
            self.player = None
            self.rank = None
            self.experience = None
            return
        self.player = NetPlayer(pm, pm.read_int(ptr + 0x8))
        self.rank = pm.read_int(ptr + 0xc)
        self.experience = pm.read_int(ptr + 0x10)

    @classmethod
    def attrs(cls):
        return super().attrs() + ['player', 'rank', 'experience']


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
        if not self.is_initialized():
            self.allowRetry = None
            self.finished = None
            return
        self.allowRetry = pm.read_bytes(ptr + 0x8, 1) == '\x01'
        self.finished = pm.read_bytes(ptr + 0x24, 1) == '\x01'

    @classmethod
    def attrs(cls):
        return super().attrs() + ['allowRetry', 'finished']


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
        if not self.is_initialized():
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
            pm, pm.read_int(ptr + 0x28),
            lambda inner_ptr: SystemString(pm, pm.read_int(inner_ptr)),
            lambda inner_ptr: GenericList(pm, pm.read_int(inner_ptr), lambda inner_ptr: PlayerMatchResult(pm, inner_ptr), 0x8))
        self._controllerIds = GenericList(
            pm, pm.read_int(ptr + 0x2c),
            lambda inner_ptr: SystemString(pm, pm.read_int(inner_ptr)))
        self._wizardIdsByPlayer = GenericList(
            pm, pm.read_int(ptr + 0x2c),
            lambda inner_ptr: pm.read_int(inner_ptr))
        self._targetScore = pm.read_int(ptr + 0x60)
        self._tournamentResultsPopup = TournamentResultsPopup(
            pm, pm.read_int(ptr + 0x34))
        # self._tournamentWinnerPopup = TournamentWinnerPopup(pm, pm.read_int(ptr + 0x38))
        # self._levelUpdatePopup = LevelUpdatePopup(pm, pm.read_int(ptr + 0x3c))
        # self._winningGameController = AbstractGameController(pm, pm.read_int(ptr + 0x40))
        self._gameModes = GenericList(
            pm, pm.read_int(ptr + 0x44),
            lambda inner_ptr: GameModeModel(pm, pm.read_int(inner_ptr)))
        self._cupType = SystemString(pm, pm.read_int(ptr + 0x48))
        self._netPlayersStartup = GenericList(
            pm, pm.read_int(ptr + 0x4c),
            lambda inner_ptr: NetPlayerAtStartup(pm, pm.read_int(inner_ptr)))
        self._defaultWin = pm.read_bytes(ptr + 0x64, 1) == '\x01'
        self._playerRanks = GenericList(
            pm, pm.read_int(ptr + 0x54),
            lambda inner_ptr: PlayerRankStruct(pm, pm.read_int(inner_ptr)))
        self._autoNext = pm.read_bytes(ptr + 0x65, 1) == '\x01'
        self._gameType = SystemString(pm, pm.read_int(ptr + 0x58))
        self._ownRank = PlayerRankStruct(pm, pm.read_int(ptr + 0x5c))
        self._friendsMatch = pm.read_bytes(ptr + 0x66, 1) == '\x01'
        self._overtime = pm.read_bytes(ptr + 0x67, 1) == '\x01'

    @classmethod
    def attrs(cls):
        return super().attrs() + [
            '_resultsByPlayer', '_controllerIds', '_wizardIdsByPlayer',
            '_targetScore', '_tournamentResultsPopup',
            '_tournamentWinnerPopup', '_levelUpdatePopup',
            '_winningGameController', '_gameModes', '_cupType',
            '_netPlayersStartup', '_defaultWin', '_playerRanks', '_autoNext',
            '_gameType', '_ownRank', '_friendsMatch', '_overtime'
        ]


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
        if not self.is_initialized():
            self.gameType = None
            self.world = None
            self.gameMode = None
            self.gameModes = None
            self.inputs = None
            self.wizardIds = None
            self.brickPacks = None
            self.selectedWizardIds = None
            self.selectedBrickPacks = None
            self.retry = None
            self.showModeTitle = None
            self.gameTypeFlowModel = None
            self.gameTypeFlow = None
            self.randomSeed = None
            self.inviteIds = None
            self.privateGame = None
            return
        self.gameType = GameTypeModel(pm, pm.read_int(ptr + 0x8))
        self.world = WorldModel(pm, pm.read_int(ptr + 0xc))
        self.gameMode = GameModeModel(pm, pm.read_int(ptr + 0x10))
        self.gameModes = GenericList(
            pm, pm.read_int(ptr + 0x14),
            lambda inner_ptr: GameModeModel(pm, pm.read_int(inner_ptr)))
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

    @classmethod
    def attrs(cls):
        return super().attrs() + [
            'gameType', 'world', 'gameMode', 'gameModes', 'inputs',
            'wizardIds', 'brickPacks', 'selectedWizardIds',
            'selectedBrickPacks', 'retry', 'showModeTitle',
            'gameTypeFlowModel', 'gameTypeFlow', 'randomSeed', 'inviteIds',
            'privateGame'
        ]


class AbstractGameTypeController(BaseModel):
    '''
    1716f180 : AbstractGameTypeController
        static fields
            0 : CONTROLLER_IDS (type: System.Collections.Generic.List<System.String>)
        fields
            8 : gameFinish (type: System.Action<System.String[],System.Single[]>)
            c : gameQuit (type: System.Action<System.String>)
            10 : retry (type: System.Action)
            14 : next (type: System.Action)
            18 : cont (type: System.Action)
            1c : _inputs (type: System.String[])
            20 : _gameSetup (type: GameSetupData)
            24 : _gameMode (type: AbstractGameMode)
            28 : _gameTypeFlow (type: AbstractGameTypeFlowController)
            2c : _gameControllers (type: System.Collections.Generic.Dictionary<System.String,AbstractGameController>)
            30 : _finishedGameControllers (type: System.Collections.Generic.List<AbstractGameController>)
            60 : _finishGame (type: System.Boolean)
            34 : _winningControllers (type: AbstractGameController[])
            38 : _winningControllerIds (type: System.String[])
            3c : _towerValues (type: System.Single[])
            40 : _gameControllersToEnd (type: System.Collections.Generic.List<System.String>)
            44 : _pauseMenu (type: PauseMenu)
            48 : _worldObjectSpawner (type: AbstractWorldObjectSpawner)
            4c : _spellCaster (type: AbstractSpellCaster)
            50 : _actionLayer (type: InputActionLayer)
            61 : _pausable (type: System.Boolean)
            54 : _fadeOutHandler (type: DG.Tweening.TweenCallback)
            62 : _fadeOutComplete (type: System.Boolean)
            58 : _fadeOutTween (type: DG.Tweening.Tweener)
            5c : _gameOverlayActivated (type: Steamworks.Callback<Steamworks.GameOverlayActivated_t>)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if not self.is_initialized():
            self._inputs = None
            self._finishGame = None
            return
        self._inputs = Array(pm, ptr + 0x1c,
                             lambda inner_ptr: SystemString(pm, inner_ptr))
        self._finishGame = pm.read_bytes(ptr + 0x60, 1) == b'\x01'

    @classmethod
    def attrs(cls):
        return super().attrs() + ['_inputs', '_finishGame']


class AbstractMultiplayerGameTypeController(AbstractGameTypeController):
    '''
    1716f180 : AbstractGameTypeController
        static fields
            0 : CONTROLLER_IDS (type: System.Collections.Generic.List<System.String>)
        fields
            8 : gameFinish (type: System.Action<System.String[],System.Single[]>)
            c : gameQuit (type: System.Action<System.String>)
            10 : retry (type: System.Action)
            14 : next (type: System.Action)
            18 : cont (type: System.Action)
            1c : _inputs (type: System.String[])
            20 : _gameSetup (type: GameSetupData)
            24 : _gameMode (type: AbstractGameMode)
            28 : _gameTypeFlow (type: AbstractGameTypeFlowController)
            2c : _gameControllers (type: System.Collections.Generic.Dictionary<System.String,AbstractGameController>)
            30 : _finishedGameControllers (type: System.Collections.Generic.List<AbstractGameController>)
            60 : _finishGame (type: System.Boolean)
            34 : _winningControllers (type: AbstractGameController[])
            38 : _winningControllerIds (type: System.String[])
            3c : _towerValues (type: System.Single[])
            40 : _gameControllersToEnd (type: System.Collections.Generic.List<System.String>)
            44 : _pauseMenu (type: PauseMenu)
            48 : _worldObjectSpawner (type: AbstractWorldObjectSpawner)
            4c : _spellCaster (type: AbstractSpellCaster)
            50 : _actionLayer (type: InputActionLayer)
            61 : _pausable (type: System.Boolean)
            54 : _fadeOutHandler (type: DG.Tweening.TweenCallback)
            62 : _fadeOutComplete (type: System.Boolean)
            58 : _fadeOutTween (type: DG.Tweening.Tweener)
            5c : _gameOverlayActivated (type: Steamworks.Callback<Steamworks.GameOverlayActivated_t>)
    17a44bf0 : AbstractMultiplayerGameTypeController
    '''
    pass


class OnlineMultiplayerGameTypeController(
        AbstractMultiplayerGameTypeController):
    '''
    1716f180 : AbstractGameTypeController
        static fields
            0 : CONTROLLER_IDS (type: System.Collections.Generic.List<System.String>)
        fields
            8 : gameFinish (type: System.Action<System.String[],System.Single[]>)
            c : gameQuit (type: System.Action<System.String>)
            10 : retry (type: System.Action)
            14 : next (type: System.Action)
            18 : cont (type: System.Action)
            1c : _inputs (type: System.String[])
            20 : _gameSetup (type: GameSetupData)
            24 : _gameMode (type: AbstractGameMode)
            28 : _gameTypeFlow (type: AbstractGameTypeFlowController)
            2c : _gameControllers (type: System.Collections.Generic.Dictionary<System.String,AbstractGameController>)
            30 : _finishedGameControllers (type: System.Collections.Generic.List<AbstractGameController>)
            60 : _finishGame (type: System.Boolean)
            34 : _winningControllers (type: AbstractGameController[])
            38 : _winningControllerIds (type: System.String[])
            3c : _towerValues (type: System.Single[])
            40 : _gameControllersToEnd (type: System.Collections.Generic.List<System.String>)
            44 : _pauseMenu (type: PauseMenu)
            48 : _worldObjectSpawner (type: AbstractWorldObjectSpawner)
            4c : _spellCaster (type: AbstractSpellCaster)
            50 : _actionLayer (type: InputActionLayer)
            61 : _pausable (type: System.Boolean)
            54 : _fadeOutHandler (type: DG.Tweening.TweenCallback)
            62 : _fadeOutComplete (type: System.Boolean)
            58 : _fadeOutTween (type: DG.Tweening.Tweener)
            5c : _gameOverlayActivated (type: Steamworks.Callback<Steamworks.GameOverlayActivated_t>)
    17a44bf0 : AbstractMultiplayerGameTypeController
    17a44b38 : OnlineMultiplayerGameTypeController
        fields
            64 : _wizardIds (type: System.Int32[])
            68 : _brickPackIds (type: System.String[])
            6c : _netPlayerGameControllers (type: System.Collections.Generic.Dictionary<NetPlayer,AbstractGameController>)
            70 : _gameControllerNetPlayers (type: System.Collections.Generic.Dictionary<AbstractGameController,NetPlayer>)
            74 : _gameModeSetupMessageHelper (type: NetworkWriterMessageHelper)
            78 : _readyMessageHelper (type: NetworkMessageHelper<UnityEngine.Networking.NetworkSystem.ReadyMessage>)
            7c : _gameStateMessageHelper (type: ServerClientNetworkMessageHelper<PlayerStringFloatMessage,TimestampedPlayerStringFloatMessage>)
            80 : _gameBaskStateMessageHelper (type: NetworkMessageHelper<BaskStateDataMessage>)
            84 : _gameEndMessageHelper (type: NetworkMessageHelper<PlayerFloatMessage>)
            88 : _gameWonMessageHelper (type: NetworkMessageHelper<GameWonMessage>)
            8c : _gameStateAtTimeMessageHelper (type: ServerClientNetworkMessageHelper<FloatMessage,PlayerStringFloatMessage>)
            90 : _audioMessageHelper (type: NetworkMessageHelper<AudioEffectMessage>)
            94 : _gameStatesAtTime (type: System.Collections.Generic.Dictionary<System.Single,System.Collections.Generic.Dictionary<AbstractGameController,System.String>>)
            98 : _dataModelSyncers (type: System.Collections.Generic.List<AbstractNetworkGameDataModelSyncer>)
            9c : _finishedTimer (type: Timer)
            a0 : _confirmPopup (type: ConfirmPopup)
            a4 : _networkErrorPopup (type: MessagePopup)
            a8 : _migrationPopup (type: HostMigrationPopup)
            ac : _gameInfoPopup (type: BasePopup)
            b0 : _gameInfoButtonPopup (type: GameInfoButtonPopup)
            b4 : _levelUpdatePopup (type: LevelUpdatePopup)
            d8 : _initialized (type: System.Boolean)
            d9 : _setupCompleted (type: System.Boolean)
            da : _allGameControllersReady (type: System.Boolean)
            db : _startGameCalled (type: System.Boolean)
            dc : _gamePlaying (type: System.Boolean)
            e0 : _lastPlayerStatusChangedCheck (type: System.Single)
            e4 : _firstPlayerStatusChangedCheck (type: System.Single)
            e8 : _readyMessageSent (type: System.Boolean)
            e9 : _gameWon (type: System.Boolean)
            ea : _gameWonMessageSent (type: System.Boolean)
            eb : _removeNetworkObjectsOnCleanup (type: System.Boolean)
            b8 : _setupConnections (type: System.Collections.Generic.List<UnityEngine.Networking.NetworkConnection>)
            bc : _gamePlayStats (type: GamePlayStats)
            c0 : _countDownEffects (type: System.Collections.Generic.List<CountDownEffect>)
            c4 : _gameModeModel (type: GameModeModel)
            c8 : _gameControllerEloScores (type: System.Collections.Generic.Dictionary<AbstractGameController,System.Int32>)
            ec : _eloScoreUpdated (type: System.Boolean)
            f0 : _inviteMode (type: GameSetupData.InviteMode)
            f4 : _hostMigrationStartedAt (type: System.Single)
            cc : _lastSentLocalGameStateRequestMessage (type: System.Collections.Generic.Dictionary<NetPlayer,TimestampedPlayerStringFloatMessage>)
            d0 : _netplayersAtStartup (type: System.Collections.Generic.List<NetPlayerAtStartup>)
            d4 : _effectRunner (type: EffectRunner)
    '''

    def __init__(self, pm, ptr):
        super().__init__(pm, ptr)
        if not self.is_initialized():
            self._gameInfoPopup = None
            self._initialized = None
            self._setupCompleted = None
            self._allGameControllersReady = None
            self._startGameCalled = None
            self._gamePlaying = None
            self._gameWon = None
            self._netPlayersStartup = None
            return
        self._gameInfoPopup = TournamentCurrentScorePopup(pm, ptr + 0xac)
        self._initialized = pm.read_bytes(ptr + 0xd8, 1) == '\x01'
        self._setupCompleted = pm.read_bytes(ptr + 0xd9, 1) == '\x01'
        self._allGameControllersReady = pm.read_bytes(ptr + 0xda, 1) == '\x01'
        self._startGameCalled = pm.read_bytes(ptr + 0xdb, 1) == '\x01'
        self._gamePlaying = pm.read_bytes(ptr + 0xdc, 1) == '\x01'
        self._gameWon = pm.read_bytes(ptr + 0xe9, 1) == '\x01'
        self._netPlayersStartup = GenericList(
            pm, pm.read_int(ptr + 0xd0),
            lambda inner_ptr: NetPlayerAtStartup(pm, pm.read_int(inner_ptr)))

    @classmethod
    def attrs(cls):
        return super().attrs() + [
            '_gameInfoPopup', '_initialized', '_setupCompleted',
            '_allGameControllersReady', '_startGameCalled', '_gamePlaying',
            '_gameWon', '_netPlayersStartup'
        ]


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
        if not self.is_initialized():
            self._gameSetup = None
            self._gameTypeController = None
            return
        self._gameSetup = GameSetupData(pm, pm.read_int(ptr + 0x24))

        # self._gameTypeController = None
        # if self._gameSetup and hasattr(
        #         self._gameSetup, 'gameType') and self._gameSetup.gameType:
        #     if self._gameSetup.gameType.is_online_multiplayer():
        #         self._gameTypeController = OnlineMultiplayerGameTypeController(
        #             pm, pm.read_int(ptr + 0x20))

    @classmethod
    def attrs(cls):
        return super().attrs() + ['_gameSetup', '_gameTypeController']
