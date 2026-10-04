import AsyncSelect from "react-select/async";

const colourStyles = {
  option: (styles: any) => {
    return {
      ...styles,
      color: "black",
    };
  },
};

export const ApiSelect = ({ setValue, apiLookup, defaultValue }: any) => {
  function handleChange(newValue: any) {
    setValue(newValue);
  }

  return (
    <AsyncSelect
      cacheOptions
      styles={colourStyles}
      loadOptions={apiLookup}
      defaultOptions={[]}
      defaultValue={defaultValue}
      onChange={handleChange}
    />
  );
};
