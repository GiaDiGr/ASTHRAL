function createNamedFunction(name,body){
 const wrapped=function(){return body.apply(this,arguments);};
 Object.defineProperty(wrapped,'name',{value:makeLegalFunctionName(name),configurable:true});
 return wrapped;
}
// END createNamedFunction
function craftInvokerFunction(humanName,argTypes,classType,cppInvokerFunc,cppTargetFunc){
 const argCount=argTypes.length;
 if(argCount<2)throwBindingError('argTypes array size mismatch! Must at least get return value and this types!');
 const method=argTypes[1]!==null&&classType!==null;
 const needsStack=argTypes.slice(1).some(type=>type!==null&&type.destructorFunction===undefined);
 return createNamedFunction(humanName,function(){
  if(arguments.length!==argCount-2)throwBindingError('function '+humanName+' called with '+arguments.length+' arguments, expected '+(argCount-2)+' args!');
  const destructors=needsStack?[]:null,wired=[];
  if(method)wired.push(argTypes[1].toWireType(destructors,this));
  for(let i=0;i<argCount-2;i++)wired.push(argTypes[i+2].toWireType(destructors,arguments[i]));
  const result=cppInvokerFunc.apply(null,[cppTargetFunc,...wired]);
  if(needsStack)runDestructors(destructors);
  else for(let i=method?1:2;i<argCount;i++)if(argTypes[i].destructorFunction!==null)argTypes[i].destructorFunction(wired[i-(method?1:2)]);
  if(argTypes[0].name!=='void')return argTypes[0].fromWireType(result);
 });
}
// END craftInvokerFunction
function __emval_get_method_caller(argCount,argTypes){
 const types=__emval_lookupTypes(argCount,argTypes),retType=types[0];
 return __emval_addMethodCaller(function(handle,name,destructors,args){
  let offset=0;const values=[];
  for(let i=1;i<argCount;i++){values.push(types[i].readValueFromPointer(args+offset));offset+=types[i].argPackAdvance;}
  const result=handle[name].apply(handle,values);
  for(let i=1;i<argCount;i++)if(types[i].deleteObject)types[i].deleteObject(values[i-1]);
  if(!retType.isVoid)return retType.toWireType(destructors,result);
 });
}
// END __emval_get_method_caller
