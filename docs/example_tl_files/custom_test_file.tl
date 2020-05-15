// test no parameters
// multiline comment
// whooo
// hey there
testTypeZero = TestTypeZero;

// test string
testTypeOne paramOne:string = TestTypeOne;

// test bool
testTypeTwo paramTwo:Bool = TestTypeTwo;

// test int32
testTypeThree paramThree:int32 = TestTypeThree;

// test int53
testTypeFour paramFour:int53 = TestTypeFour;

// test int64
testTypeFive paramFive:int64 = TestTypeFive;

// test double
testTypeSix paramSix:double = TestTypeSix;

// test bytes
testTypeSeven paramSeven:bytes = TestTypeSeven;

// test vector
testTypeEight paramEight:vector<string> = TestTypeEight;

// test nested vector
testTypeEightOne paramEight:vector<vector<string>> = TestTypeEightOne;
testTypeEightTwo paramEight:vector<vector<vector<string>>> = TestTypeEightTwo;

// test inheritance
testTypeNine paramNine:int32 = TestTypeNine;

testTypeTen paramTen:int64 = TestTypeNine;

testTypeEleven paramEleven:bool = TestTypeNine;

// test multiple
testTypeTwelve paramTwelveOne:int32 paramTwelveTwo:int53 paramTwelveThree:string paramTwelveFour:testTypeFour paramTwelveFive:TestTypeEight paramTwelveSix:vector<TestTypeEight> = TestTypeTwelve;


---functions---

// test no parameters
testFnZero = TestTypeZero;

// test string
testFnOne paramOne:string = TestTypeOne;

// test bool
testFnTwo paramTwo:Bool = TestTypeTwo;

// test int32
testFnThree paramThree:int32 = TestTypeThree;

// test int53
testFnFour paramFour:int53 = TestTypeFour;

// test int64
testFnFive paramFive:int64 = TestTypeFive;

// test double
testFnSix paramSix:double = TestTypeSix;

// test bytes
testFnSeven paramSeven:bytes = TestTypeSeven;

// test vector
testFnEight paramEight:vector<string> = TestTypeEight;

// test multiple
testFnNine paramNineOne:string paramNineTwo:Bool paramNineThree:int64 paramNineFour:bytes paramNineFive:vector<int> = TestTypeNine;



